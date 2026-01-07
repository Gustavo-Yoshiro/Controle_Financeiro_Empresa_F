from dataclasses import dataclass
from typing import Optional

@dataclass
class Inquilino:
    nome: str
    cpf: str
    telefone: str
    sexo: Optional[str] = None
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None
    email: Optional[str] = None
    obs: Optional[str] = None
    id_inquilino: Optional[int] = None