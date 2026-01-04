from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.Inquilino import Inquilino

class InquilinoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, inquilino: Inquilino) -> int:
        sql = """
            INSERT INTO inquilino (nome, cpf, estado_civil, telefone, sexo) 
            VALUES (?, ?, ?, ?, ?)
        """
        parametros = (
            inquilino.nome, 
            inquilino.cpf, 
            inquilino.estado_civil, 
            inquilino.telefone, 
            inquilino.sexo
        )
        id_gerado = self.__bd.executar(sql, parametros)
        inquilino.id_inquilino = id_gerado
        return id_gerado

    def atualizar(self, inquilino: Inquilino) -> None:
        sql = """
            UPDATE inquilino 
            SET nome=?, cpf=?, estado_civil=?, telefone=?, sexo=? 
            WHERE id_inquilino=?
        """
        parametros = (
            inquilino.nome, 
            inquilino.cpf, 
            inquilino.estado_civil, 
            inquilino.telefone, 
            inquilino.sexo, 
            inquilino.id_inquilino
        )
        self.__bd.executar(sql, parametros)

    def deletar(self, id_inquilino: int) -> None:
        sql = "DELETE FROM inquilino WHERE id_inquilino = ?"
        self.__bd.executar(sql, (id_inquilino,))

    def buscar_por_id(self, id_inquilino: int) -> Optional[Inquilino]:
        sql = "SELECT id_inquilino, nome, cpf, estado_civil, telefone, sexo FROM inquilino WHERE id_inquilino = ?"
        row = self.__bd.executar_query(sql, (id_inquilino,), fetchone=True)
        
        if row:
            return Inquilino(
                id_inquilino=row[0], 
                nome=row[1], 
                cpf=row[2], 
                estado_civil=row[3], 
                telefone=row[4], 
                sexo=row[5]
            )
        return None

    def listar_todos(self) -> List[Inquilino]:
        sql = "SELECT id_inquilino, nome, cpf, estado_civil, telefone, sexo FROM inquilino"
        rows = self.__bd.executar_query(sql)
        
        return [
            Inquilino(
                id_inquilino=r[0], nome=r[1], cpf=r[2], 
                estado_civil=r[3], telefone=r[4], sexo=r[5]
            ) for r in rows
        ]