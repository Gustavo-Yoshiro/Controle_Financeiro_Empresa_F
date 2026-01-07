from dataclasses import dataclass
from typing import Optional

@dataclass
class ContratoKitnet:
    id_contrato_kitnet: Optional[int] = None
    id_kitnet: int = 0
    id_inquilino: int = 0
    valor_fechado: float = 0.0
    data_vencimento: int = 10     
    data_inicio: str = ""         
    data_fim: Optional[str] = None
    ativo: int = 1                
    mobiliado: int = 0
    obs_mobiliado: Optional[str] = None
    pdf_caminho_contrato_kit: Optional[str] = None