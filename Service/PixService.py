from typing import List
from Persistencia.Impl.PixImpl import PixImpl
from Persistencia.Entidades.Pix import Pix

class PixService:
    def __init__(self):
        self.dao = PixImpl()

    def cadastrar_pix(self, titulo: str, chave: str, tipo: str, titular: str, banco: str) -> str:
        novo = Pix(
            titulo=titulo,
            chave=chave,
            tipo=tipo,
            titular=titular,
            banco=banco,
            favorito=0
        )
        self.dao.salvar(novo)
        return "Chave Pix salva com sucesso!"

    def alternar_favorito(self, id_pix: int, status_atual: int):
        """Se era 0 vira 1, se era 1 vira 0"""
        novo_status = 1 if status_atual == 0 else 0
        self.dao.atualizar_favorito(id_pix, novo_status)

    def excluir_pix(self, id_pix: int):
        self.dao.excluir(id_pix)

    def listar_pix(self, termo_busca: str = "") -> List[Pix]:
        """
        Retorna a lista ordenada e filtrada.
        Regra de Ouro: Favoritos no topo, depois Ordem Alfabética.
        """
        todos = self.dao.listar_todos()
        
        # 1. Filtro de Pesquisa (se tiver digitado algo)
        if termo_busca:
            termo = termo_busca.lower()
            todos = [p for p in todos if termo in p.titulo.lower() or termo in p.titular.lower()]

        # 2. Ordenação Personalizada (Lambda é vida!)
        # Explicação: Ordena primeiro por favorito (invertido, pois True > False), depois pelo titulo
        todos.sort(key=lambda x: (-x.favorito, x.titulo.lower()))
        
        return todos