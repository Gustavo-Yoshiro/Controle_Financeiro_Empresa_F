from dataclasses import dataclass
from typing import Optional


@dataclass
class Veiculo:
    id_veiculo: Optional[int] = None
    modelo: str = ""
    placa: Optional[str] = None
    ano: int = 0
    finalidade: str = 'trabalho'  # 'trabalho', 'projeto', 'revenda'
    status: str = 'ativo'         # 'ativo', 'oficina', 'vendido'
