from dataclasses import dataclass
from typing import Optional

@dataclass
class Movimentacao:
    descricao: str
    valor: float
    data_movimento: str
    id_categoria: int
    # Novos campos opcionais (default para compatibilidade)
    banco: Optional[str] = "Não Informado"
    forma_pagamento: Optional[str] = "Outro"
    
    # IDs de vínculo opcionais
    id_veiculo: Optional[int] = None
    id_pagamento_aluguel: Optional[int] = None
    id_pagamento_alocacao: Optional[int] = None
    id_divida_veiculo: Optional[int] = None
    
    id_movimentacao: Optional[int] = None