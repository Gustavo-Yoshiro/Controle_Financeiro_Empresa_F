from dataclasses import dataclass
from typing import Optional


@dataclass
class PagamentoAluguel:
    id_aluguel: Optional[int] = None
    id_contrato_kitnet: int = 0
    mes_referencia: str = ""      # Ex: "01/2026"
    valor_pago: float = 0.0
    data_pagamento: Optional[str] = None
    status: str = 'pendente'      # 'pendente', 'pago', 'atrasado'
