from __future__ import annotations

import difflib
from typing import Iterable

def _norm(value):
    return " ".join(str(value or "").lower().split())

def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()

def _same_context(new: dict, old: dict, domain: str) -> bool:
    if domain == "residency":
        return (
            _norm(new.get("institution")) == _norm(old.get("institution"))
            and _norm(new.get("state")) == _norm(old.get("state"))
        )
    return (
        _norm(new.get("organization")) == _norm(old.get("organization"))
        and _norm(new.get("state")) == _norm(old.get("state"))
    )

def build_changes(
    current: list[dict],
    previous: dict[str, dict],
    domain: str,
    fields: Iterable[str],
    revision_threshold: float = 0.78,
) -> list[dict]:
    changes: list[dict] = []
    previous_values = list(previous.values())

    for item in current:
        old = previous.get(item["id"])
        if old:
            changed = [f for f in fields if old.get(f) != item.get(f)]
            if changed:
                changes.append({
                    "type": "updated",
                    "domain": domain,
                    "id": item["id"],
                    "fields": changed,
                    "item": item,
                })
            continue

        best = None
        best_ratio = 0.0
        for candidate in previous_values:
            if not _same_context(item, candidate, domain):
                continue
            ratio = _similar(item.get("title", ""), candidate.get("title", ""))
            if ratio > best_ratio:
                best = candidate
                best_ratio = ratio

        if best and best_ratio >= revision_threshold:
            changes.append({
                "type": "revision",
                "domain": domain,
                "id": item["id"],
                "relatedId": best.get("id"),
                "similarity": round(best_ratio, 3),
                "item": item,
            })
        else:
            changes.append({
                "type": "new",
                "domain": domain,
                "id": item["id"],
                "item": item,
            })

    return changes
