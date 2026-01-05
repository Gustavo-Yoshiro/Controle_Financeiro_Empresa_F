from dataclasses import dataclass
from typing import Optional

@dataclass
class Boleto:
    descricao: str
    valor: float
    data_vencimento: str
    id_categoria: int
    codigo_barras: Optional[str] = None
    status: str = 'pendente'
    obs: Optional[str] = None
    banco_pagamento: Optional[str] = None # <--- NOVO CAMPO
    id_boleto: Optional[int] = None