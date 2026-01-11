from dataclasses import dataclass
from typing import Optional

@dataclass
class PagamentoAluguel:
    id_aluguel: Optional[int] = None
    id_contrato_kitnet: int = 0
    mes_referencia: str = ""      # Ex: "2026-01"
    valor_esperado: float = 0.0   # <--- Novo: Valor total a ser pago neste mês
    valor_pago: float = 0.0       # Quanto efetivamente entrou
    data_pagamento: Optional[str] = None
    status: str = 'pendente'      # 'pendente', 'pago', 'atrasado', 'parcial'
    obs: Optional[str] = None     # <--- Novo: Observações sobre descontos/parcial