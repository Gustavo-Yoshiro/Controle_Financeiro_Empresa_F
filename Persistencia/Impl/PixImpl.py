from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import Pix

class PixImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, pix: Pix) -> int:
        if pix.id_pix:
            # Se já tem ID, delegamos para o método atualizar
            self.atualizar(pix)
            return pix.id_pix
        else:
            sql = "INSERT INTO pix (titulo, chave, tipo, titular, banco, favorito) VALUES (?, ?, ?, ?, ?, ?)"
            params = (pix.titulo, pix.chave, pix.tipo, pix.titular, pix.banco, pix.favorito)
            pix.id_pix = self.__bd.executar(sql, params)
            return pix.id_pix

    def atualizar(self, pix: Pix) -> None:
        sql = "UPDATE pix SET titulo=?, chave=?, tipo=?, titular=?, banco=?, favorito=? WHERE id_pix=?"
        params = (pix.titulo, pix.chave, pix.tipo, pix.titular, pix.banco, pix.favorito, pix.id_pix)
        self.__bd.executar(sql, params)

    def atualizar_favorito(self, id_pix: int, status: int):
        """Muda apenas o status de favorito (0 ou 1)"""
        sql = "UPDATE pix SET favorito=? WHERE id_pix=?"
        self.__bd.executar(sql, (status, id_pix))

    def deletar(self, id_pix: int):
        sql = "DELETE FROM pix WHERE id_pix=?"
        self.__bd.executar(sql, (id_pix,))

    def listar_todos(self) -> List[Pix]:
        sql = "SELECT id_pix, titulo, chave, tipo, titular, banco, favorito FROM pix"
        rows = self.__bd.executar_query(sql)
        return [Pix(id_pix=r[0], titulo=r[1], chave=r[2], tipo=r[3], titular=r[4], banco=r[5], favorito=r[6]) for r in rows]
    
    def buscar_por_id(self, id_pix: int) -> Optional[Pix]:
        sql = "SELECT id_pix, titulo, chave, tipo, titular, banco, favorito FROM pix WHERE id_pix=?"
        row = self.__bd.executar_query(sql, (id_pix,), fetchone=True)
        if row:
            return Pix(id_pix=row[0], titulo=row[1], chave=row[2], tipo=row[3], titular=row[4], banco=row[5], favorito=row[6])
        return None

    def buscar_por_chave(self, chave: str) -> bool:
        """Retorna True se a chave já existir no banco"""
        sql = "SELECT id_pix FROM pix WHERE chave = ?"
        row = self.__bd.executar_query(sql, (chave,), fetchone=True)
        return row is not None
   

    def atualizar_favorito(self, id_pix: int, novo_status: int):
        """ Atualiza apenas o campo favorito de um Pix específico """
        sql = "UPDATE pix SET favorito = ? WHERE id_pix = ?"
        self.__bd.executar(sql, (novo_status, id_pix))