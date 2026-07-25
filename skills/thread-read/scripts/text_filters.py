from __future__ import annotations

import re
from typing import Any


_LOW_SIGNAL_PREVIEW_MARKERS = (
    "<local-command-",
    "<persisted-output",
    "<command-name>",
    "<environment_context>",
    "<permissions instructions>",
    "<collaboration_mode>",
    "<apps_instructions>",
    "<skills_instructions>",
)


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def is_meaningful_preview_candidate(value: Any) -> bool:
    normalized = normalize_text(value)
    if not normalized:
        return False

    lowered = normalized.lower()
    return not any(marker in lowered for marker in _LOW_SIGNAL_PREVIEW_MARKERS)
