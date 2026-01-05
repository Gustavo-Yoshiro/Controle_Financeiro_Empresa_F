from dataclasses import dataclass
from typing import Optional

@dataclass
class Pix:
    titulo: str
    chave: str
    tipo: str
    titular: Optional[str] = None
    banco: Optional[str] = None
    favorito: int = 0
    id_pix: Optional[int] = None