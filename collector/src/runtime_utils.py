from __future__ import annotations

import hashlib
import html
import re
import urllib.request
from datetime import date

UA = "RadarMedico/1.0 (+https://radar-medico.vercel.app)"

def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")

def clean_html(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())

def fingerprint(*parts: str) -> str:
    canonical = "|".join(" ".join((p or "").lower().split()) for p in parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def parse_deadline(text: str):
    matches = re.findall(r"(\d{2})/(\d{2})/(\d{4})", text or "")
    if not matches:
        return None
    d, m, y = matches[-1]
    try:
        return date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return None

def parse_money(text: str):
    vals = []
    for raw in re.findall(r"R\$\s*([0-9.]+(?:,[0-9]{1,2})?)", text or "", flags=re.I):
        try:
            vals.append(float(raw.replace(".", "").replace(",", ".")))
        except ValueError:
            pass
    return max(vals) if vals else None

def parse_uf(text: str) -> str:
    m = re.search(r"\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b", (text or "").upper())
    return m.group(1) if m else "BR"
