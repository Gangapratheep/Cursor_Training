"""Shared helpers for metrics payloads."""


def sanitize_error(message: str, limit: int = 180) -> str:
    """Truncate and scrub messages so local paths are not leaked unnecessarily."""
    text = " ".join((message or "Unknown error").split())
    parts = []
    for token in text.split(" "):
        if token.startswith(("/", "~")) and len(token) > 8:
            parts.append("[path]")
        else:
            parts.append(token)
    cleaned = " ".join(parts)
    if len(cleaned) > limit:
        return cleaned[: limit - 1] + "…"
    return cleaned
