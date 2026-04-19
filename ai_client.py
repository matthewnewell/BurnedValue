"""
AI client — routes to Claude (cloud) or Ollama (on-premise) based on AI_PROVIDER env var.

Usage:
    from ai_client import chat
    reply = chat(messages=[{"role": "user", "content": "..."}], system="...")

Environment variables:
    AI_PROVIDER   : "claude" | "ollama" | "none"  (default: "none")
    AI_API_KEY    : Anthropic API key (Claude only)
    AI_BASE_URL   : Ollama base URL, e.g. http://localhost:11434 (Ollama only)
    AI_MODEL      : Model name. Defaults: claude→claude-opus-4-5, ollama→llama3
"""

import os

AI_PROVIDER  = os.environ.get("AI_PROVIDER",  "none").lower()
AI_API_KEY   = os.environ.get("AI_API_KEY",   "")
AI_BASE_URL  = os.environ.get("AI_BASE_URL",  "http://localhost:11434")
AI_MODEL     = os.environ.get("AI_MODEL",     "")

_NOT_CONFIGURED = (
    "AI is not configured for this instance. "
    "Set AI_PROVIDER to 'claude' or 'ollama' in your environment or docker-compose.yml."
)


def chat(messages: list[dict], system: str = "") -> str:
    """
    Send a conversation to the configured AI and return the reply text.

    messages: list of {"role": "user"|"assistant", "content": "..."}
    system:   optional system prompt
    """
    if AI_PROVIDER == "claude":
        return _claude(messages, system)
    elif AI_PROVIDER == "ollama":
        return _ollama(messages, system)
    else:
        return _NOT_CONFIGURED


# ── Claude ────────────────────────────────────────────────────────────────────

_anthropic_client = None

def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        try:
            import anthropic
        except ImportError:
            return None
        _anthropic_client = anthropic.Anthropic(api_key=AI_API_KEY)
    return _anthropic_client


def _claude(messages: list[dict], system: str) -> str:
    client = _get_anthropic_client()
    if client is None:
        return "anthropic package not installed. Run: pip install anthropic"

    model = AI_MODEL or "claude-opus-4-5"
    kwargs = dict(model=model, max_tokens=1024, messages=messages)
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs, timeout=60)
    return response.content[0].text


# ── Ollama ────────────────────────────────────────────────────────────────────

def _ollama(messages: list[dict], system: str) -> str:
    try:
        import httpx
    except ImportError:
        return "httpx package not installed. Run: pip install httpx"

    model = AI_MODEL or "llama3"
    base  = AI_BASE_URL.rstrip("/")

    # Ollama uses OpenAI-compatible /v1/chat/completions
    payload = {
        "model": model,
        "messages": ([{"role": "system", "content": system}] if system else []) + messages,
        "stream": False,
    }

    try:
        r = httpx.post(f"{base}/v1/chat/completions", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except httpx.ConnectError:
        return f"Could not connect to Ollama at {base}. Is it running?"
    except Exception as e:
        return f"Ollama error: {e}"
