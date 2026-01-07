from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import Emprestimo

class EmprestimoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, emp: Emprestimo) -> int:
        # PADRÃO INTELIGENTE: Se tem ID, atualiza. Se não, cria.
        if emp.id_emprestimo:
            self.atualizar(emp)
            return emp.id_emprestimo
        else:
            sql = """INSERT INTO emprestimo (descricao, valor_total, valor_parcela, qtd_parcelas, 
                                             juros_mensal, data_inicio, banco_origem, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            parametros = (emp.descricao, emp.valor_total, emp.valor_parcela, emp.qtd_parcelas,
                          emp.juros_mensal, emp.data_inicio, emp.banco_origem, emp.status)
            id_gerado = self.__bd.executar(sql, parametros)
            emp.id_emprestimo = id_gerado
            return id_gerado

    def atualizar(self, emp: Emprestimo) -> None:
        sql = """UPDATE emprestimo SET descricao=?, valor_total=?, valor_parcela=?, qtd_parcelas=?, 
                 juros_mensal=?, data_inicio=?, banco_origem=?, status=? WHERE id_emprestimo=?"""
        parametros = (emp.descricao, emp.valor_total, emp.valor_parcela, emp.qtd_parcelas,
                      emp.juros_mensal, emp.data_inicio, emp.banco_origem, emp.status, emp.id_emprestimo)
        self.__bd.executar(sql, parametros)

    def deletar(self, id_emp: int) -> None:
        self.__bd.executar("DELETE FROM emprestimo WHERE id_emprestimo=?", (id_emp,))

    def buscar_por_id(self, id_emp: int) -> Optional[Emprestimo]:
        sql = """SELECT id_emprestimo, descricao, valor_total, valor_parcela, qtd_parcelas, 
                        juros_mensal, data_inicio, banco_origem, status 
                 FROM emprestimo WHERE id_emprestimo=?"""
        r = self.__bd.executar_query(sql, (id_emp,), fetchone=True)
        if r:
            return Emprestimo(id_emprestimo=r[0], descricao=r[1], valor_total=r[2], 
                              valor_parcela=r[3], qtd_parcelas=r[4], juros_mensal=r[5], 
                              data_inicio=r[6], banco_origem=r[7], status=r[8])
        return None

    def listar_todos(self) -> List[Emprestimo]:
        sql = """SELECT id_emprestimo, descricao, valor_total, valor_parcela, qtd_parcelas, 
                        juros_mensal, data_inicio, banco_origem, status 
                 FROM emprestimo ORDER BY id_emprestimo DESC"""
        rows = self.__bd.executar_query(sql)
        lista = []
        for r in rows:
            lista.append(Emprestimo(
                id_emprestimo=r[0], descricao=r[1], valor_total=r[2], 
                valor_parcela=r[3], qtd_parcelas=r[4], juros_mensal=r[5], 
                data_inicio=r[6], banco_origem=r[7], status=r[8]
            ))
        return lista