from __future__ import annotations

import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

def _csv_env(name: str) -> set[str]:
    return {x.strip().lower() for x in os.environ.get(name, "").split(",") if x.strip()}

def _passes_filters(change: dict) -> bool:
    item = change.get("item", {})
    domain = change.get("domain", "contest").lower()
    domains = _csv_env("RADAR_ALERT_DOMAINS")
    states = _csv_env("RADAR_ALERT_STATES")
    specialties = _csv_env("RADAR_ALERT_SPECIALTIES")

    if domains and domain not in domains:
        return False
    if states and str(item.get("state", "")).lower() not in states:
        return False
    if specialties:
        specialty = str(item.get("specialty", "")).lower()
        if not any(term in specialty for term in specialties):
            return False

    min_value = float(os.environ.get("RADAR_ALERT_MIN_VALUE", "0") or 0)
    value = item.get("stipend") if domain == "residency" else item.get("salary")
    if min_value and (not value or float(value) < min_value):
        return False

    return True

def main():
    runtime = Path(os.environ.get("RADAR_RUNTIME", "runtime"))
    payload = json.loads((runtime / "changes.json").read_text(encoding="utf-8"))
    changes = [c for c in payload.get("changes", []) if _passes_filters(c)]
    if not changes:
        print("Sem mudanças; nenhum e-mail enviado.")
        return

    to = os.environ.get("RADAR_EMAIL_TO", "").strip()
    user = os.environ.get("GMAIL_SMTP_USER", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not (to and user and password):
        print("Alertas por e-mail não configurados; coleta continua normalmente.")
        return

    lines = []
    for change in changes[:40]:
        item = change.get("item", {})
        kind = {"new": "NOVO", "updated": "ATUALIZADO", "revision": "RETIFICAÇÃO"}.get(change.get("type"), "ATUALIZADO")
        domain = "RESIDÊNCIA" if change.get("domain") == "residency" else "CONCURSO"
        organization = item.get("institution") or item.get("organization") or ""
        link = item.get("editalPdf") or item.get("officialUrl") or item.get("sourceUrl") or ""
        extra = ""
        if change.get("domain") == "residency":
            stipend = item.get("stipend")
            entry_type = item.get("entryType") or "tipo não informado"
            extra = f"Entrada: {entry_type}"
            if stipend:
                extra += f" | Bolsa: R$ {stipend:,.0f}".replace(",", ".")
        lines.append(
            f"[{domain} · {kind}] {item.get('title','')}\n"
            f"{organization} | {item.get('state','')} | {item.get('specialty','')}\n"
            + (f"{extra}\n" if extra else "")
            + f"Prazo: {item.get('deadline') or 'não informado'}\n{link}\n"
        )

    msg = EmailMessage()
    msg["Subject"] = f"Radar Médico: {len(changes)} alerta(s) filtrado(s)"
    msg["From"] = user
    msg["To"] = to
    msg.set_content(
        "Radar Médico — atualização automática\n\n"
        + "\n".join(lines)
        + "\n\nFontes auxiliares devem ser confirmadas no edital oficial antes de qualquer decisão."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print(f"E-mail enviado para {to}.")

if __name__ == "__main__":
    main()
