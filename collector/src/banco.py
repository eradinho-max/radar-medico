from __future__ import annotations

import difflib
from datetime import datetime, timedelta

from .modelos import Ficha, normalizar

CAMPOS_MONITORADOS = (
    "prazo", "salario", "vagas", "carga_horaria", "situacao",
    "edital_pdf", "prova", "taxa", "banca", "cargo",
)

RETIFICACAO_SIMILARIDADE_MIN = 0.78


def _herdar_timestamps(f: Ficha, anterior: dict, agora: str) -> None:
    f.primeira_vez = anterior.get("primeira_vez") or f.primeira_vez or agora
    f.ultima_atualizacao = anterior.get("ultima_atualizacao") or f.ultima_atualizacao or agora


def comparar(novos_itens: list[Ficha], dados: dict) -> tuple[list[Ficha], list[dict]]:
    agora = datetime.now().isoformat(timespec="seconds")
    itens: dict = dados.setdefault("itens", {})
    dados.setdefault("mudancas", [])
    novos: list[Ficha] = []
    atualizacoes: list[dict] = []

    for f in novos_itens:
        anterior = itens.get(f.id)
        if anterior is None:
            f.primeira_vez = f.primeira_vez or agora
            f.ultima_atualizacao = f.ultima_atualizacao or agora
            novos.append(f)
            continue

        _herdar_timestamps(f, anterior, agora)
        dif = []
        for campo in CAMPOS_MONITORADOS:
            de = anterior.get(campo)
            para = getattr(f, campo)
            if de != para and (de or para):
                dif.append({"campo": campo, "de": de, "para": para})
        if dif:
            f.ultima_atualizacao = agora
            atualizacoes.append({"ficha": f, "dif": dif, "possivel_retificacao_de": None})

    assinaturas_antigas: dict[str, list[str]] = {}
    for id_, ant in itens.items():
        chave = normalizar(f"{ant.get('orgao','')} {ant.get('uf','')}")
        assinaturas_antigas.setdefault(chave, []).append(id_)

    novos_finais: list[Ficha] = []
    for f in novos:
        chave = normalizar(f"{f.orgao} {f.uf}")
        candidatos = assinaturas_antigas.get(chave, [])
        melhor, melhor_ratio = None, 0.0
        for cand in candidatos:
            titulo_antigo = normalizar(itens[cand].get("titulo", ""))
            r = difflib.SequenceMatcher(None, normalizar(f.titulo), titulo_antigo).ratio()
            if r > melhor_ratio:
                melhor, melhor_ratio = cand, r

        if melhor and melhor_ratio >= RETIFICACAO_SIMILARIDADE_MIN:
            f.flags = sorted(set(f.flags) | {"possível retificação"})
            atualizacoes.append({
                "ficha": f,
                "dif": [{"campo": "url/edital", "de": melhor, "para": f.id}],
                "possivel_retificacao_de": melhor,
            })
        else:
            novos_finais.append(f)

    return novos_finais, atualizacoes


def incorporar(itens_novos: list[Ficha], dados: dict) -> None:
    agora = datetime.now().isoformat(timespec="seconds")
    existentes = dados.setdefault("itens", {})

    for f in itens_novos:
        anterior = existentes.get(f.id)
        if anterior:
            _herdar_timestamps(f, anterior, agora)
        else:
            f.primeira_vez = f.primeira_vez or agora
            f.ultima_atualizacao = f.ultima_atualizacao or agora
        existentes[f.id] = f.to_dict()

    limite = (datetime.now() - timedelta(days=730)).isoformat()
    preservados = {}
    for k, v in existentes.items():
        referencia = v.get("ultima_atualizacao") or v.get("primeira_vez")
        if not referencia or referencia >= limite:
            preservados[k] = v
    dados["itens"] = preservados


def registrar_mudancas(atualizacoes: list[dict], dados: dict) -> None:
    agora = datetime.now().isoformat(timespec="seconds")
    dados.setdefault("mudancas", [])
    for a in atualizacoes:
        for d in a["dif"]:
            registro = {
                "id": a["ficha"].id,
                "campo": d["campo"],
                "de": d["de"],
                "para": d["para"],
                "quando": agora,
            }
            if a.get("possivel_retificacao_de"):
                registro["possivel_retificacao_de"] = a["possivel_retificacao_de"]
            dados["mudancas"].append(registro)
    dados["mudancas"] = dados["mudancas"][-500:]
