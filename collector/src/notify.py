from __future__ import annotations

import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

def main():
    runtime = Path(os.environ.get("RADAR_RUNTIME", "runtime"))
    payload = json.loads((runtime / "changes.json").read_text(encoding="utf-8"))
    changes = payload.get("changes", [])
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
        kind = "NOVO" if change.get("type") == "new" else "ATUALIZADO"
        domain = "RESIDÊNCIA" if change.get("domain") == "residency" else "CONCURSO"
        organization = item.get("institution") or item.get("organization") or ""
        link = item.get("officialUrl") or item.get("sourceUrl") or ""
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
    msg["Subject"] = f"Radar Médico: {len(changes)} novidade(s)"
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
