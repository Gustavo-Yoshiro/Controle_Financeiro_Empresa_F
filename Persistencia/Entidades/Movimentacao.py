from dataclasses import dataclass
from typing import Optional


@dataclass
class Movimentacao:
    id_movimentacao: Optional[int] = None
    descricao: str = ""
    valor: float = 0.0
    data_movimento: str = ""
    id_categoria: int = 0
    
    # Chaves Estrangeiras Opcionais (Vínculos)
    id_veiculo: Optional[int] = None
    id_pagamento_aluguel: Optional[int] = None
    id_pagamento_alocacao: Optional[int] = None
    id_divida_veiculo: Optional[int] = None