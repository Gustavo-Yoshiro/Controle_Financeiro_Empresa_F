from dataclasses import dataclass
from typing import Optional


@dataclass
class Kitnet:
    id_kitnet: Optional[int] = None
    numero: int = 0
    quartos: int = 1
    preco_padrao: float = 0.0
    status: str = 'LIVRE' # 'LIVRE', 'OCUPADA', 'MANUTENCAO'
