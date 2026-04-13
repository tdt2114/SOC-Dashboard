from __future__ import annotations


def severity_label(level: int | None) -> str:
    if level is None:
        return "unknown"
    if level <= 3:
        return "low"
    if level <= 6:
        return "medium"
    if level <= 9:
        return "high"
    return "critical"
