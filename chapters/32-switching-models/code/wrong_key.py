"""What Gemini says to a key that isn't real. The key here is fake on purpose: never put a real key in code or on screen."""
from whitebox import GeminiModel, Message, ModelError

model = GeminiModel("gemini-3.1-flash-lite", key="not-a-real-key-demo-only")
try:
    model.chat([Message("user", "Hello")])
except ModelError as error:
    print("ModelError:", error)
    print("Worth trying again?", error.retryable)
