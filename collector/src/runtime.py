from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

from .classificador import detectar_especialidades, eh_medico
from .modelos import Ficha, normalizar
from .residencias import collect as collect_residencies
from .residency_catalog import collect_catalog_sources

UA = "RadarMedico/0.5 (+https://radar-medico.vercel.app)"

OFFICIAL_SOURCES = [
    ("ministerio-saude", "Ministério da Saúde", "https://www.gov.br/saude/pt-br/acesso-a-informacao/concursos-e-selecoes"),
    ("hu-brasil", "HU Brasil / EBSERH", "https://www.gov.br/hubrasil/pt-br/acesso-a-informacao/agentes-publicos/concursos-e-selecoes"),
]

PCI_QUERIES = [
    ("medico-clinico-geral", "Clínica Médica"),
    ("medico-da-familia", "Medicina de Família"),
    ("psiquiatra", "Psiquiatria"),
    ("geriatra", "Geriatria"),
    ("medico-do-trabalho", "Medicina do Trabalho"),
    ("medico-regulador", "Medicina de Emergência"),
    ("pediatra", "Pediatria"),
    ("ginecologista", "Ginecologia e Obstetrícia"),
    ("cardiologista", "Cardiologia"),
    ("anestesiologista", "Anestesiologia"),
    ("neurologista", "Neurologia"),
    ("ortopedista", "Ortopedia"),
    ("radiologista", "Radiologia"),
    ("urologista", "Urologia"),
    ("dermatologista", "Dermatologia"),
    ("infectologista", "Infectologia"),
]

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")

def strip_tags(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())

def fingerprint(*parts: str) -> str:
    canonical = "|".join(normalizar(p or "") for p in parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def extract_salary(text: str):
    values = []
    for raw in re.findall(r"R\$\s*([0-9.]+(?:,[0-9]{1,2})?)", text, flags=re.I):
        try:
            values.append(float(raw.replace(".", "").replace(",", ".")))
        except ValueError:
            pass
    return max(values) if values else None

def extract_uf(text: str) -> str:
    m = re.search(r"(?:-|\b)(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b", text.upper())
    return m.group(1) if m else "BR"

def extract_deadline(text: str):
    matches = re.findall(r"(\d{2})/(\d{2})/(\d{4})", text)
    if not matches:
        return None
    d, m, y = matches[-1]
    try:
        return date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return None

def status_for(deadline: str | None, text: str) -> str:
    n = normalizar(text)
    if any(x in n for x in ("previsto", "autorizado", "comissao formada")):
        return "upcoming"
    if deadline:
        try:
            return "open" if date.fromisoformat(deadline) >= date.today() else "closed"
        except ValueError:
            pass
    return "open"

def modality_for(text: str) -> str:
    n = normalizar(text)
    if "processo seletivo" in n or "selecao" in n:
        return "Processo seletivo"
    if "concurso" in n:
        return "Concurso"
    return "Outro"

def year_is_relevant(text: str) -> bool:
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    return not years or max(years) >= date.today().year - 1

def collect_govbr() -> list[dict]:
    out = []
    anchor_re = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', re.I)
    for source_id, source_name, base in OFFICIAL_SOURCES:
        try:
            page = fetch(base)
        except Exception as exc:
            print(f"[WARN] {source_id}: {exc}")
            continue
        seen = set()
        for href, inner in anchor_re.findall(page):
            title = strip_tags(inner)
            if len(title) < 8 or not year_is_relevant(title):
                continue
            absolute = urljoin(base, html.unescape(href))
            if absolute in seen:
                continue
            seen.add(absolute)
            ficha = Ficha(id="x", titulo=title, orgao=source_name, cargo=title)
            if not eh_medico(ficha):
                continue
            specs = detectar_especialidades(title)
            specialty = specs[0].replace("/", " / ").title() if specs else "Medicina"
            fp = fingerprint(source_id, title, absolute)
            out.append({
                "id": fp[:24],
                "title": title[:240],
                "organization": source_name,
                "city": "Brasil",
                "state": "BR",
                "specialty": specialty,
                "salary": None,
                "workload": None,
                "vacancies": None,
                "deadline": extract_deadline(title),
                "status": status_for(extract_deadline(title), title),
                "modality": modality_for(title),
                "officialUrl": absolute,
                "sourceUrl": absolute,
                "sourceName": source_name,
                "sourceType": "official",
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "fingerprint": fp,
            })
    return out

def _pci_cards(page: str):
    # PCI usa imagens com alt descritivo dentro dos links dos resultados.
    pat = re.compile(
        r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>\s*<img\b[^>]*alt=["\']([^"\']+)["\'][^>]*>',
        re.I,
    )
    for href, alt in pat.findall(page):
        yield html.unescape(href), html.unescape(alt)

def collect_pci() -> list[dict]:
    out = []
    seen = set()
    for query, specialty in PCI_QUERIES:
        base = f"https://www.pciconcursos.com.br/pesquisa/{query}"
        try:
            page = fetch(base)
        except Exception as exc:
            print(f"[WARN] pci:{query}: {exc}")
            continue
        for href, title in _pci_cards(page):
            absolute = urljoin(base, href)
            key = fingerprint("pci", absolute)
            if key in seen:
                continue
            seen.add(key)

            n = normalizar(title)
            if any(x in n for x in ("veterin", "biomedic", "odontolog", "dentista")):
                continue
            if not any(x in n for x in ("medic", "psiquiatr", "geriatr", "pediatr", "cardiolog", "ginecolog",
                                        "anestesiolog", "neurolog", "ortoped", "radiolog", "urolog", "dermatolog",
                                        "infectolog")):
                # A busca específica serve como descoberta, mas não publicamos título totalmente genérico.
                continue

            deadline = extract_deadline(title)
            fp = fingerprint("pci", title, absolute)
            out.append({
                "id": fp[:24],
                "title": title[:240],
                "organization": title.split(" - ")[0][:140],
                "city": "",
                "state": extract_uf(title),
                "specialty": specialty,
                "salary": extract_salary(title),
                "workload": None,
                "vacancies": None,
                "deadline": deadline,
                "status": status_for(deadline, title),
                "modality": modality_for(title),
                "officialUrl": None,
                "sourceUrl": absolute,
                "sourceName": "PCI Concursos — descoberta auxiliar",
                "sourceType": "aggregator",
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "fingerprint": fp,
            })
    return out

def dedupe(items: list[dict]) -> list[dict]:
    by_key = {}
    for item in items:
        key = item["fingerprint"]
        prev = by_key.get(key)
        if prev is None or (item["sourceType"] == "official" and prev["sourceType"] != "official"):
            by_key[key] = item
    return list(by_key.values())

def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", default="runtime")
    args = parser.parse_args()
    runtime = Path(args.runtime)
    runtime.mkdir(parents=True, exist_ok=True)

    previous_payload = load_json(runtime / "opportunities.json", {"items": []})
    previous = {i.get("id"): i for i in previous_payload.get("items", []) if i.get("id")}
    previous_residency_payload = load_json(runtime / "residencies.json", {"items": []})
    previous_residencies = {
        i.get("id"): i
        for i in previous_residency_payload.get("items", [])
        if i.get("id")
    }

    collected = dedupe(collect_govbr() + collect_pci())
    # Radar operacional: mostra abertos/futuros. Fechados ficam fora do feed.
    collected = [i for i in collected if i.get("status") in ("open", "upcoming")]
    collected.sort(key=lambda i: (i.get("deadline") or "9999-12-31", i.get("state") or "ZZ", i.get("title") or ""))

    now = datetime.now(timezone.utc).isoformat()
    changes = []
    fields = ("title","organization","state","specialty","salary","workload","vacancies","deadline","status","officialUrl","sourceUrl")
    for item in collected:
        old = previous.get(item["id"])
        if not old:
            changes.append({"type":"new","id":item["id"],"item":item})
            continue
        changed = [f for f in fields if old.get(f) != item.get(f)]
        if changed:
            changes.append({"type":"updated","id":item["id"],"fields":changed,"item":item})

    payload = {
        "updatedAt": now,
        "count": len(collected),
        "officialCount": sum(1 for i in collected if i["sourceType"] == "official"),
        "auxiliaryCount": sum(1 for i in collected if i["sourceType"] == "aggregator"),
        "items": collected,
    }
    catalog_residencies, residency_source_health = collect_catalog_sources()
    residencies = collect_residencies() + catalog_residencies
    residencies = [
        i for i in residencies
        if i.get("status") in ("open", "upcoming")
    ]
    residencies.sort(
        key=lambda i: (
            i.get("deadline") or "9999-12-31",
            i.get("state") or "ZZ",
            i.get("title") or "",
        )
    )

    residency_changes = []
    residency_fields = (
        "title", "institution", "state", "specialty", "entryType",
        "stipend", "vacancies", "deadline", "status", "examDate",
        "fee", "board", "officialUrl", "editalPdf", "sourceUrl",
    )
    for item in residencies:
        old = previous_residencies.get(item["id"])
        if not old:
            residency_changes.append({
                "type": "new",
                "domain": "residency",
                "id": item["id"],
                "item": item,
            })
            continue
        changed = [f for f in residency_fields if old.get(f) != item.get(f)]
        if changed:
            residency_changes.append({
                "type": "updated",
                "domain": "residency",
                "id": item["id"],
                "fields": changed,
                "item": item,
            })

    residency_payload = {
        "updatedAt": now,
        "count": len(residencies),
        "officialCount": sum(
            1 for i in residencies if i["sourceType"] == "official"
        ),
        "auxiliaryCount": sum(
            1 for i in residencies if i["sourceType"] == "aggregator"
        ),
        "items": residencies,
    }
    all_changes = changes + residency_changes

    save_json(runtime / "opportunities.json", payload)
    save_json(runtime / "residencies.json", residency_payload)
    save_json(runtime / "residency-source-health.json", {"updatedAt": now, "sources": residency_source_health})
    save_json(
        runtime / "changes.json",
        {"updatedAt": now, "count": len(all_changes), "changes": all_changes},
    )
    save_json(runtime / "state.json", {
        "updatedAt": now,
        "lastRun": {
            "contestsCollected": len(collected),
            "residenciesCollected": len(residencies),
            "residencySourcesChecked": len(residency_source_health),
            "residencySourcesHealthy": sum(1 for s in residency_source_health if s.get("status") == "ok"),
            "changes": len(all_changes),
        },
        "retentionNote": "Feeds públicos contêm itens abertos/futuros detectados na execução.",
    })
    print(json.dumps({
        "contests": len(collected),
        "residencies": len(residencies),
        "changes": len(all_changes),
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
