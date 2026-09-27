from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from .classificador import detectar_especialidades, eh_medico
from .modelos import Ficha, normalizar
from .runtime_utils import fetch_html, clean_html, fingerprint, parse_deadline, parse_money, parse_uf

CONFIG = Path(__file__).resolve().parents[1] / "config" / "contest_sources.json"
ACTIVE_TERMS = (
    "concurso", "processo seletivo", "seleção", "selecao", "edital",
    "chamamento", "credenciamento", "contratação", "contratacao", "vagas",
)
MEDICAL_HINTS = (
    "medico", "médico", "psiquiatr", "geriatr", "pediatr", "cardiolog",
    "clinico", "clínico", "generalista", "familia", "família", "esf",
    "plantonista", "regulador", "trabalho", "perito", "anestesiolog",
    "neurolog", "ortoped", "radiolog", "urolog", "dermatolog", "infectolog",
)
EXCLUDE = ("veterin", "biomedic", "odontolog", "dentista")

def load_sources() -> list[dict]:
    return json.loads(CONFIG.read_text(encoding="utf-8")).get("sources", [])

def _anchors(page: str):
    for href, label in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', page, flags=re.I):
        yield href, clean_html(label)

def _workload(text: str):
    m = re.search(r"(\d{1,2})\s*h(?:oras?)?\s*(?:semanais|semana|/sem)?", text, flags=re.I)
    return f"{m.group(1)}h" if m else None

def _vacancies(text: str):
    m = re.search(r"(\d+)\s*vagas?", text, flags=re.I)
    return m.group(1) if m else None

def _modality(text: str):
    n = normalizar(text)
    if "credenciamento" in n or "chamamento" in n:
        return "Outro"
    if "processo seletivo" in n or "selecao" in n:
        return "Processo seletivo"
    if "concurso" in n:
        return "Concurso"
    return "Outro"

def collect_catalog_sources() -> tuple[list[dict], list[dict]]:
    current_year = date.today().year
    opportunities: list[dict] = []
    health: list[dict] = []

    for source in load_sources():
        started = datetime.now(timezone.utc)
        try:
            page = fetch_html(source["url"])
        except Exception as exc:
            health.append({
                "id": source["id"], "name": source["name"], "url": source["url"],
                "state": source["state"], "region": source["region"], "status": "error",
                "error": str(exc), "checkedAt": datetime.now(timezone.utc).isoformat(), "matches": 0,
            })
            continue

        matches = 0
        seen = set()
        for href, label in _anchors(page):
            absolute = urljoin(source["url"], href)
            if absolute in seen:
                continue
            seen.add(absolute)
            text = f"{label} {absolute}"
            n = normalizar(text)

            if not any(normalizar(term) in n for term in ACTIVE_TERMS):
                continue
            if any(x in n for x in EXCLUDE):
                continue
            if not any(normalizar(term) in n for term in MEDICAL_HINTS):
                continue

            years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
            if years and max(years) < current_year - 1:
                continue

            ficha = Ficha(id="x", titulo=label, orgao=source["name"], cargo=label)
            if not eh_medico(ficha):
                continue

            deadline = parse_deadline(label)
            status = "open"
            if deadline:
                try:
                    status = "open" if date.fromisoformat(deadline) >= date.today() else "closed"
                except ValueError:
                    pass
            if status == "closed":
                continue

            specs = detectar_especialidades(label)
            specialty = specs[0].replace("/", " / ").title() if specs else "Medicina"
            key = fingerprint("contest-catalog", source["id"], absolute, label)

            opportunities.append({
                "id": key[:24],
                "title": (label or source["name"])[:240],
                "organization": source["name"],
                "city": source.get("city") or "",
                "state": source["state"],
                "specialty": specialty,
                "salary": parse_money(label),
                "workload": _workload(label),
                "vacancies": _vacancies(label),
                "deadline": deadline,
                "status": status,
                "modality": _modality(label),
                "officialUrl": absolute,
                "sourceUrl": source["url"],
                "sourceName": source["name"],
                "sourceType": "official",
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "fingerprint": key,
            })
            matches += 1
            if matches >= 15:
                break

        health.append({
            "id": source["id"], "name": source["name"], "url": source["url"],
            "state": source["state"], "region": source["region"], "status": "ok",
            "error": None, "checkedAt": datetime.now(timezone.utc).isoformat(),
            "matches": matches,
            "elapsedMs": int((datetime.now(timezone.utc) - started).total_seconds() * 1000),
        })

    return opportunities, health
