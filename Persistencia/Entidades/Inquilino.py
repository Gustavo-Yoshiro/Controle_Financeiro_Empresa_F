from dataclasses import dataclass
from typing import Optional


@dataclass
class Inquilino:
    id_inquilino: Optional[int] = None
    nome: str = ""
    cpf: Optional[str] = None
    estado_civil: Optional[str] = None
    telefone: Optional[str] = None
    sexo: Optional[str] = None
