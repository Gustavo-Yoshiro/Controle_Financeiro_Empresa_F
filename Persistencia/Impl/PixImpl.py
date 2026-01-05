from typing import List
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.Pix import Pix

class PixImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, pix: Pix) -> int:
        if pix.id_pix:
            # Update (caso queira editar depois)
            sql = "UPDATE pix SET titulo=?, chave=?, tipo=?, titular=?, banco=?, favorito=? WHERE id_pix=?"
            params = (pix.titulo, pix.chave, pix.tipo, pix.titular, pix.banco, pix.favorito, pix.id_pix)
            self.__bd.executar(sql, params)
        else:
            # Insert
            sql = "INSERT INTO pix (titulo, chave, tipo, titular, banco, favorito) VALUES (?, ?, ?, ?, ?, ?)"
            params = (pix.titulo, pix.chave, pix.tipo, pix.titular, pix.banco, pix.favorito)
            pix.id_pix = self.__bd.executar(sql, params)
            
        return pix.id_pix

    def atualizar_favorito(self, id_pix: int, status: int):
        """Muda apenas o status de favorito (0 ou 1)"""
        sql = "UPDATE pix SET favorito=? WHERE id_pix=?"
        self.__bd.executar(sql, (status, id_pix))

    def excluir(self, id_pix: int):
        sql = "DELETE FROM pix WHERE id_pix=?"
        self.__bd.executar(sql, (id_pix,))

    def listar_todos(self) -> List[Pix]:
        sql = "SELECT id_pix, titulo, chave, tipo, titular, banco, favorito FROM pix"
        rows = self.__bd.executar_query(sql)
        return [Pix(id_pix=r[0], titulo=r[1], chave=r[2], tipo=r[3], titular=r[4], banco=r[5], favorito=r[6]) for r in rows]