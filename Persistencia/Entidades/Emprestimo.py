from dataclasses import dataclass
from typing import Optional

@dataclass
class Emprestimo:
    descricao: str
    valor_total: float
    valor_parcela: float
    qtd_parcelas: int
    data_inicio: str
    banco_origem: str
    juros_mensal: float = 0.0
    status: str = 'ativo'
    id_emprestimo: Optional[int] = None