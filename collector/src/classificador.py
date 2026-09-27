from __future__ import annotations

import re
from datetime import date

from .modelos import Ficha, normalizar, parse_data_br

FRASES_FALSAS = (
    "medico veterinario", "medicos veterinarios",
    "biomedico", "biomedicos", "biomedicina",
    "cirurgiao dentista", "cirurgiao-dentista",
)

NAO_MEDICO = (
    "veterinari", "biomedic", "odontolog", "dentista", "enferme",
    "farmaceutic", "fisioterap", "nutricion", "psicolog", "fonoaudiolog",
    "terapia ocupacional", "assistente social", "tecnico em radiologia",
    "tecnico de enfermagem", "tecnico de laboratorio", "tecnico", "auxiliar",
    "zootecn", "motorista", "tarm", "vigilante", "agente comunitario",
    "guarda-vidas", "radiooperador", "recepcionista", "merendeira", "zelador",
)

MEDICOS = (
    "medico", "medicina", "planton", "samu", "regulador",
    "residencia medica", "clinica medica", "clinica geral", "clinico geral",
    "generalista", "estrategia de saude da familia", "saude da familia",
    "medicina de familia", "medicina da familia", "medico da familia",
    "perito medico", "medicina legal", "legista", "pericia oficial",
    "medicina do trabalho", "medicina nuclear", "medicina intensiva",
    "medicina de emergencia", "medicina de familia e comunidade",
    "medico esf", "medico psf", "cirurgiao", "anestesiolog", "cardiolog",
    "dermatolog", "endocrin", "gastroenterolog", "geriatr", "ginecolog",
    "hematolog", "infectolog", "mastolog", "neonatolog", "neurolog",
    "neurofisiolog", "obstetr", "oftalmolog", "oncolog", "ortoped",
    "otorrino", "pediatr", "pneumolog", "proctolog", "psiquiatr",
    "radiolog", "reumatolog", "urolog", "nutrolog", "angiolog",
    "hemodinam", "transplant",
)

GENERICOS_MEDICOS = {"medico", "medicina"}

ESPECIALIDADES = {
    "clinica medica": ("clinica medica", "clinica geral", "clinico geral", "generalista"),
    "medicina de familia/esf": ("estrategia de saude da familia", "saude da familia",
                                "medicina de familia", "medicina da familia",
                                "medico da familia", "medico esf", "medico psf",
                                "medicina de familia e comunidade"),
    "medico do trabalho": ("medico do trabalho", "medicina do trabalho"),
    "medico regulador": ("medico regulador", "regulador"),
    "plantonista": ("planton", "samu", "socorrista"),
    "perito medico/medicina legal": ("perito medico", "medicina legal", "legista", "pericia oficial"),
    "psiquiatria": ("psiquiatr",), "geriatria": ("geriatr",), "cardiologia": ("cardiolog",),
    "ginecologia e obstetricia": ("ginecolog", "obstetr"), "pediatria": ("pediatr", "neonatolog"),
    "anestesiologia": ("anestesiolog",), "dermatologia": ("dermatolog", "mastolog"),
    "neurologia": ("neurolog", "neurofisiolog"), "oftalmologia": ("oftalmolog",),
    "ortopedia e traumatologia": ("ortoped",), "otorrinolaringologia": ("otorrino",),
    "urologia": ("urolog",), "endocrinologia": ("endocrin",), "infectologia": ("infectolog",),
    "reumatologia": ("reumatolog",), "pneumologia": ("pneumolog",),
    "gastroenterologia": ("gastroenterolog",), "oncologia": ("oncolog",),
    "hematologia": ("hematolog",), "cirurgia geral": ("cirurgiao", "cirurgia geral"),
    "radiologia": ("radiolog",),
    "medicina intensiva/emergencia": ("medicina intensiva", "medicina de emergencia", "emergencista", "utis", "emergencia"),
    "nutrologia": ("nutrolog",), "medicina nuclear": ("medicina nuclear", "hemodinam", "transplant"),
}


def _texto_limpo(texto: str) -> str:
    alvo = normalizar(texto)
    for frase in FRASES_FALSAS:
        alvo = alvo.replace(normalizar(frase), " ")
    return " ".join(alvo.split())


def _sinais_medicos(texto: str) -> set[str]:
    alvo = _texto_limpo(texto)
    return {m for m in MEDICOS if m in alvo}


def _tem_nao_medico(texto: str) -> bool:
    alvo = normalizar(texto)
    return any(a in alvo for a in NAO_MEDICO)


def detectar_especialidades(*textos: str) -> list[str]:
    alvo = normalizar(" ".join(t or "" for t in textos))
    achadas = []
    for nome, sinonimos in ESPECIALIDADES.items():
        if any(s in alvo for s in sinonimos):
            achadas.append(nome)
    return achadas


def tem_sinal_medico(texto: str) -> bool:
    return bool(_sinais_medicos(texto))


def eh_medico(item: Ficha, ja_curado: bool = False) -> bool:
    """Nome do órgão não é evidência suficiente de vaga médica."""
    cargo = item.cargo or ""
    titulo = item.titulo or ""

    sinais_cargo = _sinais_medicos(cargo)
    sinais_titulo = _sinais_medicos(titulo)
    negativos_cargo = _tem_nao_medico(cargo)
    negativos_titulo = _tem_nao_medico(titulo)

    if sinais_cargo:
        if negativos_cargo and sinais_cargo.issubset(GENERICOS_MEDICOS):
            return False
        return True

    if sinais_titulo:
        especificos = sinais_titulo - GENERICOS_MEDICOS
        if especificos:
            return True
        if negativos_titulo:
            return False
        if re.search(r"\b(vaga|vagas|cargo|cargos|medico|medicos)\b", normalizar(titulo)):
            return True

    if ja_curado and not negativos_cargo and not negativos_titulo:
        return True

    return False


def inferir_vinculo(*textos: str) -> str:
    alvo = normalizar(" ".join(t or "" for t in textos))
    if "residencia" in alvo:
        return "residência"
    if "temporari" in alvo or "rm2" in alvo or "oficiais temporarios" in alvo:
        return "temporário"
    if "processo seletivo" in alvo or "selecao simplificada" in alvo or "selecao para" in alvo:
        return "processo seletivo"
    if "chamada publica" in alvo or "chamamento publico" in alvo:
        return "chamada pública"
    if "concurso" in alvo:
        return "concurso público"
    return "outro"


def inferir_flags(*textos: str) -> list[str]:
    alvo = normalizar(" ".join(t or "" for t in textos))
    flags = []
    if "retifica" in alvo:
        flags.append("retificado")
    if "prorroga" in alvo or "prorrogado" in alvo:
        flags.append("prorrogado")
    if "reabre" in alvo or "reaberto" in alvo or "republica" in alvo:
        flags.append("reaberto")
    return flags


def inferir_situacao(item: Ficha) -> str:
    alvo = normalizar(" ".join([item.titulo, item.prazo, item.cargo]))
    if "resultado" in alvo:
        return "resultado publicado"
    if any(p in alvo for p in ("edital autorizado", "deve ter", "previsto",
                               "preve vagas", "preve concurso", "sera organizado",
                               "tem comissao", "edital previsto")):
        return "inscricoes futuras"
    d = item.prazo_date()
    abertura = parse_data_br(item.abertura or "")
    if abertura and abertura > date.today():
        return "inscricoes futuras"
    if d is None:
        return "inscricoes abertas"
    return "inscricoes abertas" if d >= date.today() else "encerrado"
