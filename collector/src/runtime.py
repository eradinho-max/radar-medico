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
from .contest_catalog import collect_catalog_sources as collect_contest_catalog_sources
from .change_engine import build_changes

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

def _pci_article_links(page: str):
    pat = re.compile(
        r"""<a\b[^>]*href=["']([^"']*/noticias/[^"']+)["'][^>]*>([\s\S]*?)</a>""",
        re.I,
    )
    seen = set()
    for match in pat.finditer(page):
        href, inner = match.group(1), match.group(2)
        absolute = urljoin("https://www.pciconcursos.com.br", html.unescape(href))
        if absolute in seen:
            continue
        seen.add(absolute)
        label = strip_tags(inner)
        snippet = strip_tags(page[match.start(): min(len(page), match.start() + 1800)])
        yield absolute, label, snippet


def _pci_primary_text(page: str) -> str:
    text = strip_tags(page)
    markers = (
        "Compartilhe:",
        "Material Básico para Concursos",
        "Arredores:",
        "Veja também:",
        "Mapa:",
    )
    cut = len(text)
    for marker in markers:
        idx = text.find(marker)
        if idx >= 0:
            cut = min(cut, idx)
    return text[:cut]


def _pci_title_from_url(url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"-\d+$", "", slug)
    return " ".join(slug.replace("-", " ").split()).capitalize()


def _is_blocked_external(url: str) -> bool:
    low = (url or "").lower()
    return any(
        x in low
        for x in (
            "pciconcursos.com.br",
            "pci.app.br",
            "google.",
            "youtube.",
            "facebook.",
            "instagram.",
            "t.me/",
            "telegram.",
            "wa.me/",
            "whatsapp.",
            "linkedin.",
            "twitter.",
            "x.com/",
        )
    )


def _is_specific_official_url(url: str, label: str = "") -> bool:
    if not url or _is_blocked_external(url):
        return False

    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = (parsed.path or "/").lower().rstrip("/")
    query = (parsed.query or "").lower()
    evidence = normalizar(f"{label} {path} {query}")

    # Homepage/root de órgão ou banca nunca é suficiente.
    if path in ("", "/"):
        return False

    # URLs de processo/edital/seleção com identificador específico.
    specific_terms = (
        "edital",
        "concurso",
        "processo seletivo",
        "processo-seletivo",
        "selecao",
        "seleção",
        "smv",
        "rm2",
        "rm3",
        "oficial",
        "informacoes",
        "publicacoes",
        "processos-seletivos",
        "concursos-publicos",
        "aviso de convocacao",
        "aviso-de-convocacao",
    )
    if any(normalizar(term) in evidence for term in specific_terms):
        return True

    # Rotas numeradas usadas por portais oficiais/bancas, ex.: /node/100, /informacoes/35.
    if re.search(r"/(?:node|informacoes|publicacao|publicacoes|edital|processo)/[^/]+", path):
        return True

    # PDF oficial é específico por definição.
    if path.endswith(".pdf"):
        return True

    return False


def _title_keywords(title: str) -> list[str]:
    stop = {
        "abre", "abrem", "com", "para", "vagas", "vaga", "salarios", "salario",
        "publico", "publica", "edital", "concurso", "processo", "seletivo",
        "seleção", "selecao", "temporarios", "temporario", "medico", "medicos",
        "mg", "sp", "rj", "al", "rs", "sc", "pr", "brasil", "prefeitura",
        "municipal", "ate", "nivel", "superior",
    }
    words = re.findall(r"[a-z0-9ºª-]{4,}", normalizar(title))
    return [w for w in words if w not in stop][:10]


def _find_specific_link_on_page(page: str, base_url: str, title: str):
    pat = re.compile(
        r"""<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)</a>""",
        re.I,
    )
    keywords = _title_keywords(title)
    candidates = []

    for href, inner in pat.findall(page):
        absolute = urljoin(base_url, html.unescape(href))
        label = strip_tags(inner)
        if _is_blocked_external(absolute):
            continue
        if not _is_specific_official_url(absolute, label):
            continue

        evidence = normalizar(f"{label} {absolute}")
        score = 0
        if any(x in evidence for x in ("edital", "concurso", "processo seletivo", "selecao", "smv", "rm2", "rm3")):
            score += 5
        score += sum(2 for keyword in keywords if keyword in evidence)
        if str(date.today().year) in evidence or str(date.today().year + 1) in evidence:
            score += 2
        if absolute.lower().endswith(".pdf"):
            score += 2

        candidates.append((score, absolute))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score, best_url = candidates[0]
    return best_url if best_score >= 5 else None


def _pci_official_url(page: str, title: str):
    pat = re.compile(
        r"""<a\b[^>]*href=["'](https?://[^"']+)["'][^>]*>([\s\S]*?)</a>""",
        re.I,
    )
    generic_candidates = []

    for href, inner in pat.findall(page):
        url = html.unescape(href)
        label = strip_tags(inner)
        if _is_blocked_external(url):
            continue

        if _is_specific_official_url(url, label):
            return url

        generic_candidates.append(url)

    # Se o PCI só informa a homepage da banca/órgão, tenta localizar
    # a página específica do processo antes de publicar como officialUrl.
    seen = set()
    for base_url in generic_candidates[:3]:
        if base_url in seen:
            continue
        seen.add(base_url)
        try:
            external_page = fetch(base_url)
        except Exception:
            continue
        resolved = _find_specific_link_on_page(external_page, base_url, title)
        if resolved:
            return resolved

    return None


def _extract_vacancies(text: str):
    m = re.search(r"(\d+)\s*vagas?", text or "", flags=re.I)
    if m:
        return m.group(1)
    if re.search(r"\bCR\b|cadastro de reserva", text or "", flags=re.I):
        return "CR"
    return None


def collect_pci() -> list[dict]:
    base = "https://www.pciconcursos.com.br/pesquisa/medico"
    try:
        page = fetch(base)
    except Exception as exc:
        print(f"[WARN] pci:medico: {exc}")
        return []

    out = []
    for absolute, label, card_text in list(_pci_article_links(page))[:15]:
        try:
            detail_page = fetch(absolute)
        except Exception as exc:
            print(f"[WARN] pci-detail:{absolute}: {exc}")
            continue

        detail_text = strip_tags(detail_page)
        primary_text = _pci_primary_text(detail_page)
        h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", detail_page, flags=re.I)
        title = strip_tags(h1.group(1)) if h1 else ""
        if not title.strip():
            title_tag = re.search(r"<title[^>]*>([\s\S]*?)</title>", detail_page, flags=re.I)
            title = strip_tags(title_tag.group(1)) if title_tag else ""
            title = re.sub(r"\s*[-|]\s*PCI Concursos.*$", "", title, flags=re.I).strip()
        if not title.strip():
            title = _pci_title_from_url(absolute)
        if not title.strip():
            title = label or card_text[:180]

        ficha = Ficha(
            id="x",
            titulo=title,
            orgao=label,
            cargo=primary_text[:16000],
        )
        if not eh_medico(ficha):
            continue

        medical_terms = normalizar(primary_text)
        if any(
            x in medical_terms
            for x in ("medico veterinario", "biomedico")
        ) and not any(
            x in medical_terms
            for x in (
                "medico clinico",
                "medico esf",
                "medico plantonista",
                "psiquiatr",
                "geriatr",
                "pediatr",
                "cardiolog",
                "ginecolog",
                "anestesiolog",
                "neurolog",
                "ortoped",
                "urolog",
                "dermatolog",
                "infectolog",
            )
        ):
            continue

        deadline = extract_deadline(card_text)
        if deadline is None:
            insc_match = re.search(
                r"inscri[^.]{0,220}?(\d{2}/\d{2}/\d{4})",
                primary_text,
                flags=re.I,
            )
            deadline = extract_deadline(insc_match.group(0)) if insc_match else None

        status = status_for(deadline, primary_text)
        if status == "closed":
            continue

        specs = detectar_especialidades(primary_text)
        if len(specs) == 1:
            specialty = specs[0].replace("/", " / ").title()
        elif len(specs) > 1:
            specialty = "Múltiplas especialidades"
        else:
            specialty = "Medicina"

        organization = label.strip() if label.strip() else title.split(" - ")[0][:140]
        official_url = _pci_official_url(detail_page, title)
        fp = fingerprint("pci", absolute)

        out.append({
            "id": fp[:24],
            "title": title[:240],
            "organization": organization[:140],
            "city": "",
            "state": extract_uf(title + " " + card_text),
            "specialty": specialty,
            "salary": extract_salary(card_text) or extract_salary(primary_text[:12000]),
            "workload": None,
            "vacancies": _extract_vacancies(card_text),
            "deadline": deadline,
            "status": status,
            "modality": modality_for(title),
            "officialUrl": official_url,
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

    contest_catalog_items, contest_source_health = collect_contest_catalog_sources()
    collected = dedupe(collect_govbr() + collect_pci() + contest_catalog_items)
    # Radar operacional: mostra abertos/futuros. Fechados ficam fora do feed.
    collected = [i for i in collected if i.get("status") in ("open", "upcoming")]
    collected.sort(key=lambda i: (i.get("deadline") or "9999-12-31", i.get("state") or "ZZ", i.get("title") or ""))

    now = datetime.now(timezone.utc).isoformat()
    contest_fields = (
        "title","organization","state","specialty","salary","workload",
        "vacancies","deadline","status","officialUrl","sourceUrl"
    )
    changes = build_changes(
        collected,
        previous,
        domain="contest",
        fields=contest_fields,
    )

    payload = {
        "updatedAt": now,
        "count": len(collected),
        "officialCount": sum(1 for i in collected if i["sourceType"] == "official"),
        "auxiliaryCount": sum(1 for i in collected if i["sourceType"] == "aggregator"),
        "items": collected,
    }
    catalog_residencies, residency_source_health = collect_catalog_sources()
    residencies = dedupe(collect_residencies() + catalog_residencies)
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

    residency_fields = (
        "title", "institution", "state", "specialty", "entryType",
        "stipend", "vacancies", "deadline", "status", "examDate",
        "fee", "board", "officialUrl", "editalPdf", "sourceUrl",
    )
    residency_changes = build_changes(
        residencies,
        previous_residencies,
        domain="residency",
        fields=residency_fields,
    )

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
    save_json(runtime / "contest-source-health.json", {"updatedAt": now, "sources": contest_source_health})
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
            "contestSourcesChecked": len(contest_source_health),
            "contestSourcesHealthy": sum(1 for s in contest_source_health if s.get("status") == "ok"),
            "residencySourcesChecked": len(residency_source_health),
            "residencySourcesHealthy": sum(1 for s in residency_source_health if s.get("status") == "ok"),
            "changes": len(all_changes),
        },
        "retentionNote": "Feeds públicos contêm itens abertos/futuros detectados na execução.",
    })
    print(json.dumps({
        "contests": len(collected),
        "residencies": len(residencies),
        "contestSources": len(contest_source_health),
        "changes": len(all_changes),
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
