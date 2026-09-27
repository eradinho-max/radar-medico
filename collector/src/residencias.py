from __future__ import annotations

import hashlib
import html
import re
import time
import urllib.request
from datetime import date, datetime, timezone
from urllib.parse import urljoin

UA = "RadarMedico/0.6 (+https://radar-medico.vercel.app)"
PASSAPRO = "https://www.passapro.com.br/blog/editais"
ENARE_SERVICE = "https://www.gov.br/pt-br/servicos/inscrever-se-no-exame-nacional-de-residencia-enare-candidato"

EXCLUDE = (
    "multiprofissional", "uniprofissional", "enfermagem", "fisioterapia",
    "odontologia", "psicologia", "farmacia", "farmácia",
    "terapia ocupacional", "fonoaudiologia",
)

SPECIALTIES = {
    "Psiquiatria": ("psiquiatr",),
    "Geriatria": ("geriatr",),
    "Medicina de Família e Comunidade": ("medicina de familia", "medicina da familia", "mfc"),
    "Clínica Médica": ("clinica medica", "clínica médica"),
    "Cirurgia Geral": ("cirurgia geral",),
    "Pediatria": ("pediatr",),
    "Ginecologia e Obstetrícia": ("ginecolog", "obstetr"),
    "Anestesiologia": ("anestesiolog",),
    "Cardiologia": ("cardiolog",),
    "Neurologia": ("neurolog",),
    "Ortopedia e Traumatologia": ("ortoped", "traumatolog"),
    "Radiologia": ("radiolog",),
    "Oftalmologia": ("oftalmolog",),
    "Otorrinolaringologia": ("otorrino",),
    "Urologia": ("urolog",),
    "Dermatologia": ("dermatolog",),
    "Infectologia": ("infectolog",),
    "Oncologia": ("oncolog",),
    "Medicina Intensiva": ("medicina intensiva", "intensiva"),
    "Medicina de Emergência": ("medicina de emergencia", "emergencia"),
}

UF_RE = re.compile(r"\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b")

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")

def clean(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<svg[\s\S]*?</svg>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())

def normalize(value: str) -> str:
    import unicodedata
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(value.lower().split())

def fp(*parts: str) -> str:
    return hashlib.sha256("|".join(normalize(p) for p in parts).encode()).hexdigest()

def specialty_for(text: str) -> str:
    n = normalize(text)
    for name, terms in SPECIALTIES.items():
        if any(normalize(t) in n for t in terms):
            return name
    return "Múltiplas especialidades"

def parse_money(text: str):
    vals = []
    for raw in re.findall(r"R\$\s*([0-9.]+(?:,[0-9]{1,2})?)", text, flags=re.I):
        try:
            vals.append(float(raw.replace(".", "").replace(",", ".")))
        except ValueError:
            pass
    return max(vals) if vals else None

def parse_vacancies(text: str):
    m = re.search(r"(\d+)\s*vagas?", text, flags=re.I)
    return m.group(1) if m else None

def parse_uf(text: str) -> str:
    m = UF_RE.search(text.upper())
    return m.group(1) if m else "BR"

def parse_deadline(text: str):
    matches = re.findall(r"(\d{2})/(\d{2})/(\d{4})", text)
    if not matches:
        return None
    d, m, y = matches[-1]
    try:
        return date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return None

def entry_type(text: str) -> str:
    n = normalize(text)
    if "area de atuacao" in n or "área de atuação" in text.lower():
        return "Área de atuação"
    if "ano adicional" in n:
        return "Ano adicional"
    if re.search(r"\br[2-9]\b", n) or "pre-requisito" in n or "pré-requisito" in text.lower():
        return "Pré-requisito"
    if "r1" in n or "acesso direto" in n:
        return "Acesso direto"
    return "Não informado"

def detail_fields(url: str):
    try:
        page = fetch(url)
    except Exception:
        return {}
    text = clean(page)
    official = None
    for href, label in re.findall(r'<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]*>([\s\S]*?)</a>', page, flags=re.I):
        lbl = clean(label)
        if "passapro" in href:
            continue
        if re.search(r"edital|inscri|candidato", lbl, flags=re.I):
            official = html.unescape(href)
            break
    return {
        "officialUrl": official,
        "deadline": parse_deadline(text),
        "fee": parse_money(re.search(r"(?:taxa|inscri[^.]{0,40})R\$[^.]{0,30}", text, flags=re.I).group(0)) if re.search(r"(?:taxa|inscri[^.]{0,40})R\$[^.]{0,30}", text, flags=re.I) else None,
        "examDate": (re.search(r"(?:data da prova|prova)[^0-9]{0,30}(\d{2}/\d{2}/\d{4})", text, flags=re.I).group(1) if re.search(r"(?:data da prova|prova)[^0-9]{0,30}(\d{2}/\d{2}/\d{4})", text, flags=re.I) else None),
        "board": (re.search(r"(?:banca)[^A-Za-zÀ-ÿ]{0,5}([A-Za-zÀ-ÿ0-9 /.-]{2,60})", text, flags=re.I).group(1).strip() if re.search(r"(?:banca)[^A-Za-zÀ-ÿ]{0,5}([A-Za-zÀ-ÿ0-9 /.-]{2,60})", text, flags=re.I) else None),
    }

def collect_passapro(limit_details: int = 30) -> list[dict]:
    try:
        page = fetch(PASSAPRO)
    except Exception as exc:
        print(f"[WARN] residencias passapro: {exc}")
        return []

    anchor_re = re.compile(r'<a\b[^>]*href=["\'](/blog/editais/[^"\']+)["\'][^>]*>([\s\S]*?)</a>', re.I)
    out = []
    seen = set()

    for href, body in anchor_re.findall(page):
        body_text = clean(body)
        n = normalize(body_text)
        if "residencia" not in n:
            continue
        if any(normalize(x) in n for x in EXCLUDE):
            continue
        if "especialista" in n or "prova de titulo" in n or "exame de especialista" in n:
            continue

        title_match = re.search(r"<h3[^>]*>([\s\S]*?)</h3>", body, flags=re.I)
        title = clean(title_match.group(1)) if title_match else body_text[:180]
        if not title:
            continue

        org_match = re.search(r"<p[^>]*>([^<]+)</p>", body, flags=re.I)
        institution = clean(org_match.group(1)) if org_match else ""
        source_url = urljoin(PASSAPRO, href)
        if source_url in seen:
            continue
        seen.add(source_url)

        status = "upcoming" if "EM BREVE" in body else "open" if "INSCRIÇÕES ABERTAS" in body else "closed"
        if status == "closed":
            continue

        detail = detail_fields(source_url) if len(out) < limit_details else {}
        time.sleep(0.15 if len(out) < limit_details else 0)
        deadline = detail.get("deadline")
        if deadline:
            try:
                status = "open" if date.fromisoformat(deadline) >= date.today() else "closed"
            except ValueError:
                pass
        if status == "closed":
            continue

        combined = f"{title} {institution} {body_text}"
        key = fp("residencia", title, institution, source_url)
        out.append({
            "id": key[:24],
            "title": title[:240],
            "institution": institution[:180],
            "city": "",
            "state": parse_uf(combined),
            "specialty": specialty_for(combined),
            "entryType": entry_type(combined),
            "stipend": parse_money(body_text),
            "vacancies": parse_vacancies(body_text),
            "deadline": deadline,
            "status": status,
            "examDate": detail.get("examDate"),
            "fee": detail.get("fee"),
            "board": detail.get("board"),
            "officialUrl": detail.get("officialUrl"),
            "sourceUrl": source_url,
            "sourceName": "PassaPro — descoberta auxiliar",
            "sourceType": "official" if detail.get("officialUrl") else "aggregator",
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "fingerprint": key,
        })

    return out

def collect_enare_reference() -> list[dict]:
    # Registro de referência oficial. Só aparece quando não houver deadline vencido;
    # serve para rastreabilidade do processo nacional, sem inventar edital aberto.
    return [{
        "id": fp("enare-reference", ENARE_SERVICE)[:24],
        "title": "ENARE — Exame Nacional de Residência",
        "institution": "HU Brasil / Governo Federal",
        "city": "Brasil",
        "state": "BR",
        "specialty": "Múltiplas especialidades",
        "entryType": "Acesso direto / Pré-requisito / Área de atuação",
        "stipend": None,
        "vacancies": None,
        "deadline": None,
        "status": "reference",
        "examDate": None,
        "fee": None,
        "board": None,
        "officialUrl": ENARE_SERVICE,
        "sourceUrl": ENARE_SERVICE,
        "sourceName": "Governo Federal — ENARE",
        "sourceType": "official",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "fingerprint": fp("enare-reference", ENARE_SERVICE),
    }]

def collect() -> list[dict]:
    items = collect_passapro()
    # A referência oficial fica separada do feed aberto para não parecer inscrição ativa.
    return items
