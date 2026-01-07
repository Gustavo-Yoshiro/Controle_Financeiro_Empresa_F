from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import Inquilino

class InquilinoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, inquilino: Inquilino) -> int:
        # PADRÃO INTELIGENTE: Se tem ID, atualiza. Se não, cria.
        if inquilino.id_inquilino:
            self.atualizar(inquilino)
            return inquilino.id_inquilino
        else:
            sql = """
                INSERT INTO inquilino (nome, cpf, telefone, estado_civil, profissao, sexo, email, obs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            parametros = (
                inquilino.nome, inquilino.cpf, inquilino.telefone, 
                inquilino.estado_civil, inquilino.profissao, 
                inquilino.sexo, inquilino.email, inquilino.obs
            )
            id_gerado = self.__bd.executar(sql, parametros)
            inquilino.id_inquilino = id_gerado
            return id_gerado

    def atualizar(self, inquilino: Inquilino):
        sql = """
            UPDATE inquilino 
            SET nome=?, cpf=?, telefone=?, estado_civil=?, profissao=?, sexo=?, email=?, obs=?
            WHERE id_inquilino=?
        """
        parametros = (
            inquilino.nome, inquilino.cpf, inquilino.telefone, 
            inquilino.estado_civil, inquilino.profissao, 
            inquilino.sexo, inquilino.email, inquilino.obs,
            inquilino.id_inquilino
        )
        self.__bd.executar(sql, parametros)

    def deletar(self, id_inquilino: int):
        self.__bd.executar("DELETE FROM inquilino WHERE id_inquilino=?", (id_inquilino,))

    def buscar_por_id(self, id_inq: int) -> Optional[Inquilino]:
        sql = "SELECT id_inquilino, nome, cpf, telefone, estado_civil, profissao, sexo, email, obs FROM inquilino WHERE id_inquilino=?"
        row = self.__bd.executar_query(sql, (id_inq,), fetchone=True)
        if row:
            return Inquilino(
                id_inquilino=row[0], nome=row[1], cpf=row[2], telefone=row[3],
                estado_civil=row[4], profissao=row[5], sexo=row[6], email=row[7], obs=row[8]
            )
        return None

    def listar_todos(self) -> List[Inquilino]:
        sql = "SELECT id_inquilino, nome, cpf, telefone, estado_civil, profissao, sexo, email, obs FROM inquilino ORDER BY nome"
        rows = self.__bd.executar_query(sql)
        return [
            Inquilino(
                id_inquilino=r[0], nome=r[1], cpf=r[2], telefone=r[3], 
                estado_civil=r[4], profissao=r[5], sexo=r[6], email=r[7], obs=r[8]
            ) for r in rows
        ]