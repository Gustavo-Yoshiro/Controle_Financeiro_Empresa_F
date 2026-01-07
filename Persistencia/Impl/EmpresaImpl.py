from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import Empresa

class EmpresaImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, empresa: Empresa) -> int:
        # PADRÃO INTELIGENTE: Se tem ID, atualiza. Se não, cria.
        if empresa.id_empresa:
            self.atualizar(empresa)
            return empresa.id_empresa
        else:
            sql = "INSERT INTO empresa (razao_social, cnpj, telefone) VALUES (?, ?, ?)"
            parametros = (empresa.razao_social, empresa.cnpj, empresa.telefone)
            id_gerado = self.__bd.executar(sql, parametros)
            empresa.id_empresa = id_gerado
            return id_gerado
    
    def atualizar(self, empresa: Empresa) -> None:
        sql = "UPDATE empresa SET razao_social=?, cnpj=?, telefone=? WHERE id_empresa=?"
        parametros = (empresa.razao_social, empresa.cnpj, empresa.telefone, empresa.id_empresa)
        self.__bd.executar(sql, parametros)

    def deletar(self, id_empresa: int) -> None:
        sql = "DELETE FROM empresa WHERE id_empresa = ?"
        self.__bd.executar(sql, (id_empresa,))

    def listar_todas(self) -> List[Empresa]:
        sql = "SELECT id_empresa, razao_social, cnpj, telefone FROM empresa"
        rows = self.__bd.executar_query(sql)
        return [Empresa(id_empresa=r[0], razao_social=r[1], cnpj=r[2], telefone=r[3]) for r in rows]

    def buscar_por_id(self, id_empresa: int) -> Optional[Empresa]:
        sql = "SELECT id_empresa, razao_social, cnpj, telefone FROM empresa WHERE id_empresa=?"
        row = self.__bd.executar_query(sql, (id_empresa,), fetchone=True)
        if row:
            return Empresa(id_empresa=row[0], razao_social=row[1], cnpj=row[2], telefone=row[3])
        return None