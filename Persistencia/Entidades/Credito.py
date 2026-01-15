from dataclasses import dataclass
from typing import Optional

@dataclass
class CartaoCredito:
    id_cartao: Optional[int] = None
    nome: str = ""
    dia_fechamento: int = 1
    dia_vencimento: int = 10
    limite: float = 0.0
    bandeira: str = ""
