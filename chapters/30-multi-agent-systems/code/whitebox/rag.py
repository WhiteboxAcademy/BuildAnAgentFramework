"""RAG: find the right passages, then answer from them."""
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import requests

from .agent import Result
from .messages import Message
from .models import ModelError
from .tools import tool

DEFAULT_EMBEDDER = "nomic-embed-text"


class Embedder:
    """The shape that every embedding model shares."""

    def embed_documents(self, texts):
        raise NotImplementedError

    def embed_query(self, text):
        raise NotImplementedError


class OllamaEmbedder(Embedder):
    """An embedding model served by Ollama."""

    def __init__(self, name=DEFAULT_EMBEDDER, url="http://127.0.0.1:11434", batch=64):
        self.name = name
        self.url = url
        self.batch = batch

    def embed(self, texts):
        """Send texts in batches, because one huge request can fail."""
        vectors = []
        for start in range(0, len(texts), self.batch):
            vectors += self.embed_batch(texts[start:start + self.batch])
        return vectors

    def embed_batch(self, texts):
        body = {"model": self.name, "input": texts}
        try:
            response = requests.post(f"{self.url}/api/embed", json=body, timeout=180)
        except requests.RequestException as error:
            raise ModelError(f"Couldn't reach Ollama: {error}", retryable=True) from error
        if not response.ok:
            raise ModelError(f"Ollama said {response.status_code}: {response.text}", response.status_code >= 500)
        return response.json()["embeddings"]

    def embed_documents(self, texts):
        return self.embed([f"search_document: {text}" for text in texts])

    def embed_query(self, text):
        return self.embed([f"search_query: {text}"])[0]


class FakeEmbedder(Embedder):
    """Counts words into a fixed list of slots. Texts that share words end up close."""

    def __init__(self, size=64):
        self.size = size

    def vector(self, text):
        slots = [0.0] * self.size
        for word in words(text):
            slots[sum(map(ord, word)) % self.size] += 1.0
        return slots

    def embed_documents(self, texts):
        return [self.vector(text) for text in texts]

    def embed_query(self, text):
        return self.vector(text)


def words(text):
    return re.findall(r"[a-z0-9-]+", text.lower())


def cosine(a, b):
    """How closely two vectors point the same way: 1 is identical, 0 is unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    size = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / size if size else 0.0


@dataclass
class Chunk:
    text: str
    source: str


@dataclass
class Hit:
    text: str
    source: str
    score: float


class VectorStore:
    """Keeps every vector in a list, and compares a query with all of them."""

    def __init__(self):
        self.rows = []

    def add(self, chunks, vectors):
        self.rows += [(chunk, vector) for chunk, vector in zip(chunks, vectors)]

    def search(self, vector, k=5):
        hits = [Hit(chunk.text, chunk.source, cosine(vector, row)) for chunk, row in self.rows]
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:k]

    def save(self, path):
        data = [{"text": chunk.text, "source": chunk.source, "vector": vector} for chunk, vector in self.rows]
        Path(path).write_text(json.dumps(data))

    def load(self, path):
        data = json.loads(Path(path).read_text())
        self.rows = [(Chunk(row["text"], row["source"]), row["vector"]) for row in data]


class ChromaStore(VectorStore):
    """The same two methods, backed by the Chroma vector database."""

    def __init__(self, path, name="handbook"):
        import chromadb

        client = chromadb.PersistentClient(path=str(path))
        self.collection = client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})

    def add(self, chunks, vectors):
        start = self.collection.count()
        self.collection.add(
            ids=[str(start + number) for number in range(len(chunks))],
            embeddings=vectors,
            documents=[chunk.text for chunk in chunks],
            metadatas=[{"source": chunk.source} for chunk in chunks],
        )

    def search(self, vector, k=5):
        found = self.collection.query(query_embeddings=[vector], n_results=k)
        rows = zip(found["documents"][0], found["metadatas"][0], found["distances"][0])
        return [Hit(text, data["source"], 1 - distance) for text, data, distance in rows]


def load_documents(folder):
    """Read every Markdown file in a folder into a dict of name to text."""
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(Path(folder).glob("*.md"))}


def split_text(text, size=120):
    """Split on blank lines, then join paragraphs until a piece reaches about size words."""
    pieces, current = [], []
    for paragraph in re.split(r"\n\s*\n", text.strip()):
        if current and len(" ".join(current).split()) + len(paragraph.split()) > size:
            pieces.append("\n\n".join(current))
            current = []
        current.append(paragraph)
    pieces.append("\n\n".join(current))
    return pieces


def make_chunks(documents, size=120, titles=False):
    """Split documents into chunks. With titles, each chunk starts with its document's title."""
    chunks = []
    for name, text in documents.items():
        title = text.splitlines()[0].lstrip("# ")
        for piece in split_text(text, size):
            starts_with_title = piece.startswith("#")
            chunks.append(Chunk(f"{title}\n\n{piece}" if titles and not starts_with_title else piece, name))
    return chunks


class Index:
    """Embeds chunks into a store, and embeds questions to search it."""

    def __init__(self, embedder, store=None):
        self.embedder = embedder
        self.store = store if store is not None else VectorStore()

    def add(self, chunks):
        self.store.add(chunks, self.embedder.embed_documents([chunk.text for chunk in chunks]))

    def search(self, question, k=5):
        return self.store.search(self.embedder.embed_query(question), k)


RAG_SYSTEM = (
    "Answer the question using only the excerpts below. "
    "After the answer, name the file you used in brackets, such as [uniform.md]. "
    "If the excerpts don't contain the answer, say exactly: I don't know."
)


def excerpts(hits):
    return "\n\n".join(f"[{hit.source}]\n{hit.text}" for hit in hits)


@dataclass
class Rag:
    """The pipeline: search once, put the hits in the prompt, and ask the model."""

    model: object
    index: object
    k: int = 5
    options: dict = field(default_factory=dict)

    def run(self, question):
        hits = self.index.search(question, self.k)
        messages = [
            Message("system", RAG_SYSTEM),
            Message("user", f"Excerpts:\n\n{excerpts(hits)}\n\nQuestion: {question}"),
        ]
        reply = self.model.chat(messages, **self.options)
        return Result(reply.content, messages + [reply], 1)


class KeywordIndex:
    """BM25: scores chunks by the rare words they share with the question."""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.chunks = []
        self.counts = []
        self.seen_in = Counter()

    def add(self, chunks):
        for chunk in chunks:
            counts = Counter(words(chunk.text))
            self.chunks.append(chunk)
            self.counts.append(counts)
            self.seen_in.update(counts.keys())

    def rarity(self, word):
        total = len(self.chunks)
        return math.log(1 + (total - self.seen_in[word] + 0.5) / (self.seen_in[word] + 0.5))

    def score(self, question_words, counts, average):
        length = sum(counts.values())
        total = 0.0
        for word in question_words:
            found = counts[word]
            scale = 1 - self.b + self.b * length / average
            total += self.rarity(word) * found * (self.k1 + 1) / (found + self.k1 * scale)
        return total

    def search(self, question, k=5):
        average = sum(sum(counts.values()) for counts in self.counts) / len(self.counts)
        question_words = set(words(question))
        scores = [self.score(question_words, counts, average) for counts in self.counts]
        hits = [Hit(chunk.text, chunk.source, score) for chunk, score in zip(self.chunks, scores) if score > 0]
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:k]


class HybridIndex:
    """Joins several rankings. A chunk scores more the higher it ranks in each one."""

    def __init__(self, indexes, depth=20, damping=60):
        self.indexes = indexes
        self.depth = depth
        self.damping = damping

    def add(self, chunks):
        for index in self.indexes:
            index.add(chunks)

    def search(self, question, k=5):
        found = {}
        for index in self.indexes:
            for rank, hit in enumerate(index.search(question, self.depth), start=1):
                best = found.setdefault(hit.text, Hit(hit.text, hit.source, 0.0))
                best.score += 1 / (self.damping + rank)
        return sorted(found.values(), key=lambda hit: hit.score, reverse=True)[:k]


class Reranker:
    """Fetches more hits than needed, then asks a model to score each against the question."""

    def __init__(self, index, model, depth=15):
        self.index = index
        self.model = model
        self.depth = depth

    def add(self, chunks):
        self.index.add(chunks)

    def judge(self, question, hit):
        prompt = (
            f"Question: {question}\n\nPassage:\n{hit.text}\n\n"
            "Does the passage help answer the question? Reply with one number from 0 (no) to 10 (yes)."
        )
        reply = self.model.chat([Message("user", prompt)], temperature=0)
        found = re.search(r"\d+", reply.content)
        return int(found.group()) if found else 0

    def search(self, question, k=5):
        hits = self.index.search(question, self.depth)
        scored = [Hit(hit.text, hit.source, self.judge(question, hit)) for hit in hits]
        return sorted(scored, key=lambda hit: hit.score, reverse=True)[:k]


def hit_rate(index, cases, k=5):
    """The share of cases where every needed file appears in the top k. cases: (question, files)."""
    found = 0
    for question, files in cases:
        sources = {hit.source for hit in index.search(question, k)}
        found += all(name in sources for name in files)
    return found, len(cases)


def search_tool(index, k=3):
    """Turn an index into a tool, so an agent can decide what to look up."""

    @tool
    def search_handbook(query: Annotated[str, "What to look up, in a few words"]) -> str:
        """Search the staff handbook. Search again with new words if the result isn't enough."""
        return excerpts(index.search(query, k)) or "Nothing found."

    return search_handbook


AGENT_SYSTEM = (
    "You answer questions about the Quillon Coffee staff handbook. Use search_handbook to find facts, "
    "and never answer from memory. One search may not be enough: if an answer depends on a second fact, "
    "such as a band or a branch's contractor, search for that too. "
    "After the answer, name the file you used in brackets, such as [uniform.md]. "
    "If searching doesn't find the answer, say exactly: I don't know."
)
