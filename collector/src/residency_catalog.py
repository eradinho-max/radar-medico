from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from .residencias import clean, fetch, fp, normalize, parse_deadline, parse_money, parse_vacancies, specialty_for, entry_type

CONFIG = Path(__file__).resolve().parents[1] / "config" / "residency_sources.json"
ACTIVE_TERMS = ("edital", "processo seletivo", "seleção", "selecao", "inscrições", "inscricoes", "vagas", "remanescente", "residência médica", "residencia medica")
EXCLUDE_TERMS = ("multiprofissional", "uniprofissional", "odontologia", "enfermagem", "fisioterapia", "psicologia", "farmácia", "farmacia")
ACCESSORY_TERMS = ("resultado", "gabarito", "convocacao", "convocação", "recurso", "homologacao", "homologação", "classificacao", "classificação", "segunda chamada", "chamada final", "adendo", "confirmacao de inscricoes", "confirmação de inscrições", "local de prova", "comprovante de inscricao", "comprovante de inscrição", "errata", "retificacao", "retificação")
GENERIC_LABELS = ("abrir", "download", "clique aqui", "ver arquivo", "arquivo")

def load_sources() -> list[dict]:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    return data.get("sources", [])

def _anchors(page: str):
    for href, label in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', page, flags=re.I):
        yield href, clean(label)

def collect_catalog_sources() -> tuple[list[dict], list[dict]]:
    year = date.today().year
    years = (str(year), str(year + 1))
    opportunities: list[dict] = []
    health: list[dict] = []

    for source in load_sources():
        started = datetime.now(timezone.utc)
        try:
            page = fetch(source["url"])
            status = "ok"
            error = None
        except Exception as exc:
            health.append({
                "id": source["id"], "name": source["name"], "url": source["url"],
                "state": source["state"], "region": source["region"], "status": "error",
                "error": str(exc), "checkedAt": datetime.now(timezone.utc).isoformat(),
                "matches": 0,
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
            n = normalize(text)

            if any(normalize(x) in n for x in ACCESSORY_TERMS):
                continue
            found_years = [int(y) for y in re.findall(r"20\d{2}", text)]
            if found_years and max(found_years) < year:
                continue
            if normalize(label) in {normalize(x) for x in GENERIC_LABELS}:
                url_name = absolute.rsplit("/", 1)[-1].split("?")[0].replace("-", " ").replace("_", " ")
                if not any(term in normalize(url_name) for term in ("edital", "residencia medica", "processo seletivo", "inscricoes", "vagas remanescentes")):
                    continue
                label = url_name

            if "residencia" not in n or "medic" not in n:
                continue
            if any(normalize(x) in n for x in EXCLUDE_TERMS) and "residencia medica" not in n:
                continue
            if not any(normalize(x) in n for x in ACTIVE_TERMS):
                continue
            if not any(y in text for y in years) and not any(x in n for x in ("inscricoes abertas", "inscrições abertas", "remanescente", "vagas")):
                continue

            deadline = parse_deadline(label)
            item_status = "open"
            if deadline:
                try:
                    item_status = "open" if date.fromisoformat(deadline) >= date.today() else "closed"
                except ValueError:
                    pass
            if item_status == "closed":
                continue

            key = fp("catalog-residency", source["id"], absolute, label)
            opportunities.append({
                "id": key[:24],
                "title": (label or source["name"])[:240],
                "institution": source["name"],
                "city": source["city"],
                "state": source["state"],
                "specialty": specialty_for(label),
                "entryType": entry_type(label),
                "stipend": parse_money(label),
                "vacancies": parse_vacancies(label),
                "deadline": deadline,
                "status": item_status,
                "examDate": None,
                "fee": None,
                "board": None,
                "officialUrl": absolute,
                "editalPdf": absolute if absolute.lower().endswith(".pdf") else None,
                "sourceUrl": source["url"],
                "sourceName": source["name"],
                "sourceType": "official",
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "fingerprint": key,
            })
            matches += 1
            if matches >= 12:
                break

        health.append({
            "id": source["id"], "name": source["name"], "url": source["url"],
            "state": source["state"], "region": source["region"], "status": status,
            "error": error, "checkedAt": datetime.now(timezone.utc).isoformat(),
            "matches": matches,
            "elapsedMs": int((datetime.now(timezone.utc)-started).total_seconds()*1000),
        })
    return opportunities, health
