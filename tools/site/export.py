"""Export chapter pages to the website repo, and write each video's YouTube details.

usage: python3 tools/site/export.py SITE_REPO

Add a chapter by adding it to videos.json. Paste a YouTube video ID there once it's uploaded,
then run this again. Run it from the course folder.
"""
import json
import re
import shutil
import sys
from pathlib import Path

COURSE = "Build an AI Agent from Scratch"
SITE_PATH = "/courses/build-an-ai-agent"
SITE_URL = f"https://whiteboxacademy.in{SITE_PATH}"
REPO = "https://github.com/WhiteboxAcademy/BuildAnAgentFramework"
YOUTUBE = "https://www.youtube.com/@WhiteboxAcademy"
OLD_START_LINK = "https://claude.ai/artifact/1uGgX3WK7v3D5HyfvB782p#start-ollama"
START_LINK = f"{SITE_PATH}/00-setup/#start-ollama"
VIDEOS = json.loads((Path(__file__).parent / "videos.json").read_text())

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Whitebox Academy</title>
<meta name="description" content="{dek}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{dek}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="article">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap">
<link rel="stylesheet" href="/assets/site.css">
<link rel="stylesheet" href="/assets/chapter.css">
<script>document.documentElement.classList.add("js")</script>
<script src="/assets/site.js" defer></script>
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/"><i></i>Whitebox Academy</a>
    <button class="menu-button" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
    <nav class="site-nav" id="site-nav" aria-label="Chapter">
      <a href="{site_path}/">Course</a>
      <a href="{site_path}/#curriculum">Curriculum</a>
      <a href="{code}">Code</a>
      <a class="nav-cta" href="{youtube}">Follow on YouTube</a>
    </nav>
  </div>
</header>
"""

FOOT = """<footer class="site-footer">
  <div class="wrap">
    <span>© 2026 Whitebox Academy · Code MIT · Articles &amp; videos CC BY 4.0</span>
    <nav aria-label="Footer">
      <a href="/">Home</a>
      <a href="{youtube}">YouTube</a>
      <a href="https://github.com/WhiteboxAcademy">GitHub</a>
    </nav>
  </div>
</footer>
</body>
</html>
"""


def read_page(slug):
    """Return the parts of a chapter's page."""
    page = (Path("chapters") / slug / "page" / "index.html").read_text()
    main = re.search(r'<main class="gutter">\s*<div class="wrap">(.*)</div>\s*</main>', page, re.S).group(1)
    video, article = main.split("</section>", 1)
    return {
        "meta": re.search(r'<span class="meta">(.*?)</span>', page).group(1),
        "title": re.search(r"<h1>(.*?)</h1>", page).group(1),
        "dek": re.search(r'<p class="dek">(.*?)</p>', page).group(1),
        "poster": re.search(r'poster="(.*?)"', video).group(1),
        "caption": re.search(r"<figcaption>(.*?)</figcaption>", video).group(1),
        "article": re.sub(r"\s*<footer>.*?</footer>", "", article, flags=re.S),
    }


def plain(text):
    return re.sub(r"<[^>]+>", "", text).replace("’", "'")


def video_block(page):
    video_id = VIDEOS[page["slug"]]
    if video_id:
        media = (f'<iframe src="https://www.youtube-nocookie.com/embed/{video_id}" title="{plain(page["title"])}" '
                 'loading="lazy" allowfullscreen></iframe>')
    else:
        media = (f'<img src="{page["poster"]}" alt="" width="1440" height="900">'
                 '<span class="video-soon">Video coming soon</span>')
    return f'<figure class="chapter-video"><div class="video-frame">{media}</div><figcaption>{page["caption"]}</figcaption></figure>'


def link_next(article, next_page):
    """Turn the next-chapter block into a link, if that chapter is on the site."""
    if not next_page:
        return article
    pattern = r'<div class="next"><span>Next</span><h3>(.*?)</h3></div>'
    href = f'{SITE_PATH}/{next_page["slug"]}/'
    return re.sub(pattern, rf'<a class="next" href="{href}"><span>Next</span><h3>\1</h3></a>', article)


def write_chapter(site, page, next_page):
    slug = page["slug"]
    url = f"{SITE_URL}/{slug}/"
    code = f"{REPO}/tree/main/chapters/{slug}"
    folder = site / SITE_PATH.strip("/") / slug
    (folder / "media").mkdir(parents=True, exist_ok=True)
    article = link_next(page["article"].replace(OLD_START_LINK, START_LINK), next_page)
    html = HEAD.format(title=plain(page["title"]), dek=plain(page["dek"]), url=url, site_path=SITE_PATH,
                       code=code, youtube=YOUTUBE)
    html += f"""
<main class="chapter">
  <section class="chapter-hero dark grid-bg">
    <div class="wrap">
      <p class="chapter-meta">{page["meta"]}</p>
      <h1>{page["title"]}</h1>
      <p class="lede">{page["dek"]}</p>
      <div class="actions"><a class="button hot" href="{code}">Get this chapter’s code</a></div>
    </div>
  </section>
  <div class="wrap chapter-body">
    {video_block(page)}
    {article.strip()}
  </div>
</main>

"""
    (folder / "index.html").write_text(html + FOOT.format(youtube=YOUTUBE))
    for name in re.findall(r'media/([\w.-]+\.jpg)', html):
        shutil.copy(Path("chapters") / slug / "media" / name, folder / "media" / name)


def write_youtube_details(page):
    slug = page["slug"]
    number = slug[:2]
    text = f"""# YouTube details: chapter {number}

**File to upload:** `chapters/{slug}/media/video.mp4`

**Title:**

{plain(page["title"])} | {COURSE}, Chapter {number}

**Description:**

{plain(page["dek"])}

This is chapter {number} of {COURSE}, a free, self-paced course from Whitebox Academy. The video is silent, with captions on screen.

Article and exercises: {SITE_URL}/{slug}/
Course code: {REPO}/tree/main/chapters/{slug}
Full course: {SITE_URL}/

The code is under the MIT License, and this video is under CC BY 4.0.

**Playlist:** {COURSE}

**Settings:** Not made for kids. Choose the Creative Commons license. Add the video to the playlist.
"""
    (Path("chapters") / slug / "video" / "youtube.md").write_text(text)


def main():
    site = Path(sys.argv[1])
    pages = []
    for slug in VIDEOS:
        page = read_page(slug)
        page["slug"] = slug
        pages.append(page)
    for index, page in enumerate(pages):
        next_page = pages[index + 1] if index + 1 < len(pages) else None
        write_chapter(site, page, next_page)
        write_youtube_details(page)
        print(f"Exported {page['slug']}")
    # The final-project roll page reads the ideas from its own copy, so keep it the same as the course's.
    roll_page = site / SITE_PATH.lstrip("/") / "final-project"
    if roll_page.exists():
        shutil.copy(Path("final-project") / "projects.json", roll_page / "projects.json")
        print("Copied final-project/projects.json")


if __name__ == "__main__":
    main()
