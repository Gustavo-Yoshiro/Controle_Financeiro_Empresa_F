from dataclasses import dataclass
from typing import Optional


@dataclass
class Categoria:
    id_categoria: Optional[int] = None
    nome: str = ""
    tipo: str = 'despesa'  # 'receita' ou 'despesa'
