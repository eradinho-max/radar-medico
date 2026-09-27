from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().split())


def parse_data_br(texto: str) -> Optional[date]:
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto or "")
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


@dataclass
class Ficha:
    id: str
    titulo: str = ""
    orgao: str = ""
    municipio: str = ""
    uf: str = "BR"
    cargo: str = ""
    especialidades: list = field(default_factory=list)
    vagas: str = ""
    cadastro_reserva: bool = False
    carga_horaria: str = ""
    salario: Optional[float] = None
    taxa: Optional[float] = None
    abertura: Optional[str] = None
    prazo: str = ""
    prazo_data: Optional[str] = None
    prova: str = ""
    banca: str = ""
    fonte: str = ""
    url: str = ""
    edital_pdf: str = ""
    vinculo: str = ""
    situacao: str = ""
    flags: list = field(default_factory=list)
    primeira_vez: str = ""
    ultima_atualizacao: str = ""

    def prazo_date(self) -> Optional[date]:
        if self.prazo_data:
            try:
                return date.fromisoformat(self.prazo_data)
            except ValueError:
                return None
        return parse_data_br(self.prazo)

    def vencido(self) -> bool:
        d = self.prazo_date()
        return bool(d and d < date.today())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Ficha":
        campos = {f for f in Ficha.__dataclass_fields__}
        return Ficha(**{k: v for k, v in d.items() if k in campos})
