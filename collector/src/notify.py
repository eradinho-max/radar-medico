from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

PROFILE_PATH = Path(__file__).resolve().parents[1] / "config" / "my_radar.json"


def load_profile() -> dict:
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "enabled": True,
            "domains": ["contest", "residency"],
            "states": [],
            "specialties": [],
            "contest_min_salary": 0,
            "residency_min_stipend": 0,
            "only_open": True,
            "official_only": False,
            "notify_new": True,
            "notify_updates": True,
            "notify_revisions": True,
            "digest": "immediate",
        }


def _specialty_match(value: str, wanted: list[str]) -> bool:
    if not wanted:
        return True
    normalized = (value or "").lower()
    return any(term.lower() in normalized for term in wanted)


def _passes_filters(change: dict, profile: dict) -> bool:
    if not profile.get("enabled", True):
        return False

    item = change.get("item", {})
    domain = change.get("domain", "contest")
    change_type = change.get("type", "updated")

    domains = profile.get("domains") or []
    if domains and domain not in domains:
        return False

    if change_type == "new" and not profile.get("notify_new", True):
        return False
    if change_type == "updated" and not profile.get("notify_updates", True):
        return False
    if change_type == "revision" and not profile.get("notify_revisions", True):
        return False

    states = profile.get("states") or []
    if states and item.get("state") not in states:
        return False

    if not _specialty_match(
        str(item.get("specialty", "")),
        profile.get("specialties") or [],
    ):
        return False

    if profile.get("only_open", True) and item.get("status") != "open":
        return False

    if profile.get("official_only", False):
        has_official = bool(
            item.get("editalPdf")
            or item.get("officialUrl")
            or item.get("sourceType") == "official"
        )
        if not has_official:
            return False

    if domain == "residency":
        minimum = float(profile.get("residency_min_stipend") or 0)
        value = item.get("stipend")
    else:
        minimum = float(profile.get("contest_min_salary") or 0)
        value = item.get("salary")

    if minimum and (value is None or float(value) < minimum):
        return False

    return True


def _digest_allowed(profile: dict) -> bool:
    if profile.get("digest") != "daily":
        return True
    # A coleta roda 3x/dia. No modo diário, apenas a janela da manhã UTC envia.
    hour = datetime.now(timezone.utc).hour
    return 9 <= hour <= 11


def main():
    runtime = Path(os.environ.get("RADAR_RUNTIME", "runtime"))
    payload = json.loads((runtime / "changes.json").read_text(encoding="utf-8"))
    profile = load_profile()

    if not _digest_allowed(profile):
        print("Perfil em resumo diário; esta execução não é a janela de envio.")
        return

    changes = [
        change
        for change in payload.get("changes", [])
        if _passes_filters(change, profile)
    ]

    if not changes:
        print("Sem mudanças compatíveis com Meu Radar; nenhum e-mail enviado.")
        return

    to = os.environ.get("RADAR_EMAIL_TO", "").strip()
    user = os.environ.get("GMAIL_SMTP_USER", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not (to and user and password):
        print("E-mail ainda não configurado; coleta e Meu Radar continuam funcionando.")
        return

    lines = []
    for change in changes[:50]:
        item = change.get("item", {})
        kind = {
            "new": "NOVO",
            "updated": "ATUALIZADO",
            "revision": "RETIFICAÇÃO",
        }.get(change.get("type"), "ATUALIZADO")

        is_residency = change.get("domain") == "residency"
        domain = "RESIDÊNCIA" if is_residency else "CONCURSO"
        organization = item.get("institution") or item.get("organization") or ""
        link = (
            item.get("editalPdf")
            or item.get("officialUrl")
            or item.get("sourceUrl")
            or ""
        )

        extra = ""
        if is_residency:
            entry_type = item.get("entryType") or "tipo não informado"
            extra = f"Entrada: {entry_type}"
            stipend = item.get("stipend")
            if stipend:
                extra += f" | Bolsa: R$ {stipend:,.0f}".replace(",", ".")
        else:
            salary = item.get("salary")
            if salary:
                extra = f"Remuneração: R$ {salary:,.0f}".replace(",", ".")

        lines.append(
            f"[{domain} · {kind}] {item.get('title','')}\n"
            f"{organization} | {item.get('state','')} | {item.get('specialty','')}\n"
            + (f"{extra}\n" if extra else "")
            + f"Prazo: {item.get('deadline') or 'não informado'}\n"
            + f"{link}\n"
        )

    msg = EmailMessage()
    msg["Subject"] = f"Radar Médico: {len(changes)} alerta(s) do Meu Radar"
    msg["From"] = user
    msg["To"] = to
    msg.set_content(
        "Meu Radar — oportunidades compatíveis com seu perfil\n\n"
        + "\n".join(lines)
        + "\n\nConfira regras, requisitos e prazos no edital correspondente."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)

    print(f"Meu Radar: {len(changes)} alerta(s) enviados para {to}.")


if __name__ == "__main__":
    main()
