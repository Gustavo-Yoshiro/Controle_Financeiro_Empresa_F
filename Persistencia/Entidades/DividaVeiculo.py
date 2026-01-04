from dataclasses import dataclass
from typing import Optional


@dataclass
class DividaVeiculo:
    id_divida: Optional[int] = None
    id_veiculo: int = 0
    descricao: str = ""
    valor: float = 0.0
    data_vencimento: Optional[str] = None
    status: str = 'pendente'
