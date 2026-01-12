from dataclasses import dataclass
from typing import Optional

@dataclass
class ContratoAlocacao:
    id_contrato_alocacao: Optional[int] = None
    id_empresa: int = 0
    id_veiculo: int = 0
    valor_mensal: float = 0.0
    dia_vencimento: int = 10
    ativo: int = 1
    
    data_inicio: str = "" 
    
    data_fim: Optional[str] = None