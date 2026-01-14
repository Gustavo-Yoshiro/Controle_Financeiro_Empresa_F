from dataclasses import dataclass
from typing import Optional

@dataclass
class Boleto:
    descricao: str
    valor: float
    data_vencimento: str
    id_categoria: int
    
    codigo_barras: str = ""
    status: str = 'pendente'
    obs: str = ""
    banco_pagamento: str = "" 
    
   
    banco_cartao: Optional[str] = None 
    
    id_boleto: Optional[int] = None