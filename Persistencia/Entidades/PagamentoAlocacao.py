from dataclasses import dataclass
from typing import Optional


@dataclass
class PagamentoAlocacao:
    id_pagamento_alocacao: Optional[int] = None
    id_contrato_alocacao: int = 0
    mes_referencia: str = ""
    valor_esperado: float = 0.0
    status: str = 'pendente'
    data_pagamento: Optional[str] = None
