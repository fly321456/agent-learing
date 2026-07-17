from __future__ import annotations

import json
import re
from typing import Any


MAX_LOG_STRING_CHARS = 2_000
MAX_LOG_COLLECTION_ITEMS = 50

_SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|authorization|cookie|password|secret|token)",
    re.IGNORECASE,
)
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]+=*", re.IGNORECASE),
    re.compile(
        r"\b(api[_-]?key|password|secret|token)\s*[:=]\s*[^\s,;]+",
        re.IGNORECASE,
    ),
)


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in _SENSITIVE_VALUE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def sanitize_for_logging(value: Any, *, key: str | None = None) -> Any:
    """Return a bounded, secret-safe projection suitable for events and logs."""
    if key is not None and _SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        redacted = _redact_text(value)
        if len(redacted) <= MAX_LOG_STRING_CHARS:
            return redacted
        return {
            "value": redacted[:MAX_LOG_STRING_CHARS],
            "truncated": True,
            "original_chars": len(redacted),
        }
    if isinstance(value, dict):
        items = list(value.items())
        projected = {
            str(item_key): sanitize_for_logging(item, key=str(item_key))
            for item_key, item in items[:MAX_LOG_COLLECTION_ITEMS]
        }
        if len(items) > MAX_LOG_COLLECTION_ITEMS:
            projected["_truncated"] = True
            projected["_original_items"] = len(items)
        return projected
    if isinstance(value, (list, tuple)):
        projected = [
            sanitize_for_logging(item)
            for item in value[:MAX_LOG_COLLECTION_ITEMS]
        ]
        if len(value) > MAX_LOG_COLLECTION_ITEMS:
            projected.append(
                {"truncated": True, "original_items": len(value)}
            )
        return projected
    return sanitize_for_logging(str(value), key=key)


def format_for_approval(arguments: dict[str, Any]) -> str:
    return json.dumps(
        sanitize_for_logging(arguments),
        ensure_ascii=False,
        sort_keys=True,
    )
