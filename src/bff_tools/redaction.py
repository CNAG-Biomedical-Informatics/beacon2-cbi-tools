from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit


SENSITIVE_KEY_PARTS = ("password", "passwd", "secret", "token", "api_key", "apikey")


def redact_uri(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "<redacted>"
    if not parsed.scheme or parsed.hostname is None or parsed.username is None:
        return value

    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, f"<redacted>@{host}", parsed.path, parsed.query, parsed.fragment))


def redact_value(value: Any, *, key: str = "") -> Any:
    lowered = key.lower()
    if any(part in lowered for part in SENSITIVE_KEY_PARTS):
        return "<redacted>"
    if lowered.endswith("uri") and isinstance(value, str):
        return redact_uri(value)
    if isinstance(value, Mapping):
        return {str(child_key): redact_value(child_value, key=str(child_key)) for child_key, child_value in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    return value


def redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): redact_value(item, key=str(key)) for key, item in value.items()}
