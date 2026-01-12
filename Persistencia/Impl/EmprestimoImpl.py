from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import Emprestimo

class EmprestimoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, emp: Emprestimo) -> int:
        if emp.id_emprestimo:
            self.atualizar(emp)
            return emp.id_emprestimo
        else:
            # ADICIONADO: data_primeira_parcela no INSERT
            sql = """
                INSERT INTO emprestimo 
                (descricao, valor_total, valor_parcela, qtd_parcelas, juros_mensal, 
                 data_inicio, data_primeira_parcela, banco_origem, valor_pago, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            parametros = (
                emp.descricao, 
                emp.valor_total, 
                emp.valor_parcela, 
                emp.qtd_parcelas, 
                emp.juros_mensal, 
                emp.data_inicio, 
                emp.data_primeira_parcela, # <--- NOVO
                emp.banco_origem,
                emp.valor_pago,
                emp.status
            )
            id_gerado = self.__bd.executar(sql, parametros)
            emp.id_emprestimo = id_gerado
            return id_gerado

    def atualizar(self, emp: Emprestimo) -> None:
        # ADICIONADO: data_primeira_parcela no UPDATE
        sql = """
            UPDATE emprestimo 
            SET descricao=?, valor_total=?, valor_parcela=?, qtd_parcelas=?, 
                juros_mensal=?, data_inicio=?, data_primeira_parcela=?, 
                banco_origem=?, valor_pago=?, status=? 
            WHERE id_emprestimo=?
        """
        parametros = (
            emp.descricao, 
            emp.valor_total, 
            emp.valor_parcela, 
            emp.qtd_parcelas, 
            emp.juros_mensal, 
            emp.data_inicio, 
            emp.data_primeira_parcela, # <--- NOVO
            emp.banco_origem,
            emp.valor_pago,
            emp.status,
            emp.id_emprestimo
        )
        self.__bd.executar(sql, parametros)

    def listar_todos(self) -> List[Emprestimo]:
        # ADICIONADO: data_primeira_parcela no SELECT (índice 7)
        sql = """
            SELECT id_emprestimo, descricao, valor_total, valor_parcela, qtd_parcelas, 
                   juros_mensal, data_inicio, data_primeira_parcela, banco_origem, valor_pago, status 
            FROM emprestimo
        """
        rows = self.__bd.executar_query(sql)
        return [
            Emprestimo(
                id_emprestimo=r[0], 
                descricao=r[1], 
                valor_total=r[2], 
                valor_parcela=r[3], 
                qtd_parcelas=r[4], 
                juros_mensal=r[5], 
                data_inicio=r[6], 
                data_primeira_parcela=r[7], # <--- NOVO
                banco_origem=r[8], 
                valor_pago=r[9] if r[9] is not None else 0.0,
                status=r[10]
            ) for r in rows
        ]

    def buscar_por_id(self, id_emp: int) -> Optional[Emprestimo]:
        # ADICIONADO: data_primeira_parcela no SELECT WHERE ID
        sql = """
            SELECT id_emprestimo, descricao, valor_total, valor_parcela, qtd_parcelas, 
                   juros_mensal, data_inicio, data_primeira_parcela, banco_origem, valor_pago, status 
            FROM emprestimo WHERE id_emprestimo = ?
        """
        row = self.__bd.executar_query(sql, (id_emp,), fetchone=True)
        if row:
            return Emprestimo(
                id_emprestimo=row[0], 
                descricao=row[1], 
                valor_total=row[2], 
                valor_parcela=row[3], 
                qtd_parcelas=row[4], 
                juros_mensal=row[5], 
                data_inicio=row[6], 
                data_primeira_parcela=row[7], # <--- NOVO
                banco_origem=row[8], 
                valor_pago=row[9] if row[9] is not None else 0.0,
                status=row[10]
            )
        return None
    
    def deletar(self, id_emp: int):
        self.__bd.executar("DELETE FROM emprestimo WHERE id_emprestimo=?", (id_emp,))