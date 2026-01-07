from dataclasses import dataclass
from typing import Optional

@dataclass
class Kitnet:
    numero: int
    quartos: int = 1
    preco_padrao: float = 0.0
    status: str = 'LIVRE'
    identificador: str = 'K' 
    id_kitnet: Optional[int] = None