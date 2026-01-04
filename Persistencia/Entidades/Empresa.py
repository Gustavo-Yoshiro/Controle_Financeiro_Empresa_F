from dataclasses import dataclass
from typing import Optional


@dataclass
class Empresa:
    id_empresa: Optional[int] = None
    razao_social: str = ""
    cnpj: Optional[str] = None
    telefone: Optional[str] = None
