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

OFFICIAL_OPEN_PAGES = [
    {
        "name": "SES/SC — Escola de Saúde Pública",
        "url": "https://esp.saude.sc.gov.br/index.php/todos-os-cursos/771-processo-seletivo-programas-de-residencia-medica",
        "state": "SC",
        "city": "Santa Catarina",
        "specialty": "Múltiplas especialidades",
        "entryType": "Acesso direto / Pré-requisito",
        "knownDeadline": "2026-10-19",
    },
    {
        "name": "Prefeitura de Joinville — Residência Médica",
        "url": "https://www.joinville.sc.gov.br/publicacoes/processo-seletivo-edital-no-30568243-2026-para-residencia-medica-em-medicina-de-familia-e-comunidade/",
        "state": "SC",
        "city": "Joinville",
        "specialty": "Medicina de Família e Comunidade",
        "entryType": "Acesso direto",
        "knownDeadline": "2026-10-19",
    },
    {
        "name": "SESAU/RO — COREME",
        "url": "https://rondonia.ro.gov.br/publicacao/edital-no-14-2026-cohrec-coreme/",
        "state": "RO",
        "city": "Rondônia",
        "specialty": "Múltiplas especialidades",
        "entryType": "Não informado",
        "knownDeadline": None,
    },
    {
        "name": "UFFS — COREME Passo Fundo",
        "url": "https://boletim.uffs.edu.br/atos-normativos/edital/coremepf/2026-0036",
        "state": "RS",
        "city": "Passo Fundo",
        "specialty": "Múltiplas especialidades",
        "entryType": "Acesso direto / Pré-requisito",
        "knownDeadline": None,
    },
    {
        "name": "UFFS — COREME Chapecó",
        "url": "https://boletim.uffs.edu.br/atos-normativos/edital/coremech/2026-0011",
        "state": "SC",
        "city": "Chapecó",
        "specialty": "Múltiplas especialidades",
        "entryType": "Acesso direto / Pré-requisito",
        "knownDeadline": None,
    },
    {
        "name": "UCPel / HUSFP — COREME",
        "url": "https://ucpel.edu.br/noticias/ucpel-e-husfp-abrem-inscricoes-para-residencia-medica-2027",
        "state": "RS",
        "city": "Pelotas",
        "specialty": "Múltiplas especialidades",
        "entryType": "Acesso direto / Pré-requisito",
        "knownDeadline": "2026-10-19",
        "knownVacancies": "61",
    },
    {
        "name": "UNIFIPA — Residência Médica",
        "url": "https://unifipa.edu.br/editais",
        "state": "SP",
        "city": "Catanduva",
        "specialty": "Múltiplas especialidades",
        "entryType": "Não informado",
        "knownDeadline": None,
    },
    {
        "name": "HU Brasil / CH-UFC — Residência Médica",
        "url": "https://www.gov.br/hubrasil/pt-br/hospitais-universitarios/regiao-nordeste/ch-ufc/ensino-e-pesquisa/editais-1/residencia-1/EDITALN012026RESMEDVAGASNOOCUPADASNOENARE24022026.pdf",
        "state": "CE",
        "city": "Fortaleza",
        "specialty": "Múltiplas especialidades",
        "entryType": "Área de atuação / Ano adicional",
        "knownDeadline": None,
        "knownVacancies": "8",
    },
    {
        "name": "HU Brasil / CHU-UFPA — Residência Médica",
        "url": "https://www.gov.br/hubrasil/pt-br/hospitais-universitarios/regiao-norte/chu-ufpa/ensino-e-pesquisa/processo-seletivo/pss-medica-2026/v-processo-seletivo-simplificado-de-residencia-medica-2026.pdf/view",
        "state": "PA",
        "city": "Belém",
        "specialty": "Múltiplas especialidades",
        "entryType": "Não informado",
        "knownDeadline": None,
    },
    {
        "name": "HU Brasil / HUL-UFS — ENARE",
        "url": "https://www.gov.br/hubrasil/pt-br/hospitais-universitarios/regiao-nordeste/hul-ufs/locais-de-prova-do-enare-e-enamed-2026-ja-podem-ser-consultados-2",
        "state": "SE",
        "city": "Aracaju / Lagarto",
        "specialty": "Múltiplas especialidades",
        "entryType": "Acesso direto / Pré-requisito",
        "knownDeadline": None,
    },
]

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


def _extract_first_official_document(page: str, base_url: str):
    for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', page, flags=re.I):
        lbl = clean(label)
        absolute = urljoin(base_url, html.unescape(href))
        target = (lbl + " " + absolute).lower()
        if absolute.lower().endswith(".pdf"):
            return absolute
        if re.search(r"\bedital\b", target, flags=re.I) and absolute != base_url:
            return absolute
    return None

def _parse_exam_date(text: str):
    m = re.search(r"(?:data da prova|prova(?: objetiva)?)[^0-9]{0,40}(\d{2}/\d{2}/\d{4})", text, flags=re.I)
    return m.group(1) if m else None

def _parse_fee(text: str):
    m = re.search(r"(?:taxa|inscri[^.]{0,50})[^R$]{0,15}R\$\s*([0-9.]+(?:,[0-9]{1,2})?)", text, flags=re.I)
    if not m:
        return None
    try:
        return float(m.group(1).replace(".", "").replace(",", "."))
    except ValueError:
        return None

def collect_official_pages() -> list[dict]:
    out = []
    for source in OFFICIAL_OPEN_PAGES:
        try:
            page = fetch(source["url"])
        except Exception as exc:
            print(f"[WARN] residencia oficial {source['name']}: {exc}")
            continue

        text = clean(page)
        n = normalize(text)
        if "residencia medica" not in n and "medico residente" not in n:
            continue
        if "encerrad" in n and not source.get("knownDeadline"):
            continue

        deadline = source.get("knownDeadline") or parse_deadline(text)
        status = "open"
        if deadline:
            try:
                status = "open" if date.fromisoformat(deadline) >= date.today() else "closed"
            except ValueError:
                pass
        if status == "closed":
            continue

        title_match = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", page, flags=re.I)
        title = clean(title_match.group(1)) if title_match else source["name"]
        edital_pdf = _extract_first_official_document(page, source["url"])
        key = fp("official-residency", source["url"], title)

        out.append({
            "id": key[:24],
            "title": title[:240],
            "institution": source["name"],
            "city": source["city"],
            "state": source["state"],
            "specialty": source["specialty"],
            "entryType": source["entryType"],
            "stipend": None,
            "vacancies": source.get("knownVacancies") or parse_vacancies(text),
            "deadline": deadline,
            "status": status,
            "examDate": _parse_exam_date(text),
            "fee": _parse_fee(text),
            "board": None,
            "officialUrl": source["url"],
            "editalPdf": edital_pdf,
            "sourceUrl": source["url"],
            "sourceName": source["name"],
            "sourceType": "official",
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "fingerprint": key,
        })
    return out

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
            "editalPdf": detail.get("officialUrl") if (detail.get("officialUrl") or "").lower().endswith(".pdf") else None,
            "sourceUrl": source_url,
            "sourceName": "PassaPro — descoberta auxiliar",
            "sourceType": "aggregator",
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
    official = collect_official_pages()
    auxiliary = collect_passapro()

    seen = {item["officialUrl"] for item in official if item.get("officialUrl")}
    merged = list(official)
    for item in auxiliary:
        if item.get("officialUrl") and item["officialUrl"] in seen:
            continue
        merged.append(item)
    return merged
