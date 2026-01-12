from dataclasses import dataclass
from typing import Optional

@dataclass
class Emprestimo:
    descricao: str
    valor_total: float
    valor_parcela: float
    qtd_parcelas: int
    juros_mensal: float
    data_inicio: str        
    data_primeira_parcela: str 
    banco_origem: str
    
    valor_pago: float = 0.0
    status: str = 'ativo'
    id_emprestimo: Optional[int] = None