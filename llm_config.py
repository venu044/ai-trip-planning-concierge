"""
Connects to a local Ollama model, the same way the lab notebooks do.

Swap MODEL_NAME for whatever you pulled locally, e.g.:
    ollama pull qwen2.5:3b
"""

from langchain_ollama import ChatOllama

MODEL_NAME = "qwen2.5:3b"


def get_llm(temperature: float = 0.0) -> ChatOllama:
    """Return a chat model connected to the local Ollama server."""
    return ChatOllama(model=MODEL_NAME, temperature=temperature)
