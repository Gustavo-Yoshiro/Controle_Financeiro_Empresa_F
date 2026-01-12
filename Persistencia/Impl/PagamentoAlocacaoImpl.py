from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import PagamentoAlocacao

class PagamentoAlocacaoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, pag: PagamentoAlocacao) -> int:
        # Se tem ID, atualiza. Se não, cria.
        if pag.id_pagamento_alocacao:
            self.atualizar(pag)
            return pag.id_pagamento_alocacao
        else:
            # --- CORREÇÃO 1: Adicionado valor_pago no INSERT ---
            sql = """
                INSERT INTO pagamento_alocacao 
                (id_contrato_alocacao, mes_referencia, valor_esperado, valor_pago, status, data_pagamento) 
                VALUES (?, ?, ?, ?, ?, ?)
            """
            parametros = (
                pag.id_contrato_alocacao,
                pag.mes_referencia,
                pag.valor_esperado,
                pag.valor_pago, 
                pag.status,
                pag.data_pagamento
            )
            id_gerado = self.__bd.executar(sql, parametros)
            pag.id_pagamento_alocacao = id_gerado
            return id_gerado

    def atualizar(self, pag: PagamentoAlocacao) -> None:
        # --- CORREÇÃO 2: Adicionado valor_pago no UPDATE ---
        sql = """
            UPDATE pagamento_alocacao 
            SET id_contrato_alocacao=?, mes_referencia=?, valor_esperado=?, valor_pago=?, status=?, data_pagamento=? 
            WHERE id_pagamento_alocacao=?
        """
        parametros = (
            pag.id_contrato_alocacao,
            pag.mes_referencia,
            pag.valor_esperado,
            pag.valor_pago,
            pag.status,
            pag.data_pagamento,
            pag.id_pagamento_alocacao
        )
        self.__bd.executar(sql, parametros)
        
    def deletar(self, id_pagamento: int) -> None:
        sql = "DELETE FROM pagamento_alocacao WHERE id_pagamento_alocacao = ?"
        self.__bd.executar(sql, (id_pagamento,))

    def buscar_por_id(self, id_pagamento: int) -> Optional[PagamentoAlocacao]:
        # --- CORREÇÃO 3: Adicionado valor_pago no SELECT ---
        sql = """
            SELECT id_pagamento_alocacao, id_contrato_alocacao, mes_referencia, valor_esperado, valor_pago, status, data_pagamento 
            FROM pagamento_alocacao WHERE id_pagamento_alocacao = ?
        """
        row = self.__bd.executar_query(sql, (id_pagamento,), fetchone=True)
        if row:
            return PagamentoAlocacao(
                id_pagamento_alocacao=row[0], 
                id_contrato_alocacao=row[1], 
                mes_referencia=row[2], 
                valor_esperado=row[3], 
                valor_pago=row[4], 
                status=row[5], 
                data_pagamento=row[6]
            )
        return None

    def listar_pendentes(self) -> List[PagamentoAlocacao]:
        # Aqui também precisamos ler o valor_pago para saber quanto JÁ foi pago da dívida
        sql = """
            SELECT id_pagamento_alocacao, id_contrato_alocacao, mes_referencia, valor_esperado, valor_pago, status, data_pagamento 
            FROM pagamento_alocacao WHERE status IN ('pendente', 'atrasado', 'parcial')
        """
        rows = self.__bd.executar_query(sql)
        return [
            PagamentoAlocacao(
                id_pagamento_alocacao=r[0], id_contrato_alocacao=r[1], mes_referencia=r[2], 
                valor_esperado=r[3], valor_pago=r[4], status=r[5], data_pagamento=r[6]
            ) for r in rows
        ]
        
    def listar_todos(self) -> List[PagamentoAlocacao]:
        sql = "SELECT id_pagamento_alocacao, id_contrato_alocacao, mes_referencia, valor_esperado, valor_pago, status, data_pagamento FROM pagamento_alocacao"
        rows = self.__bd.executar_query(sql)
        return [
            PagamentoAlocacao(
                id_pagamento_alocacao=r[0], 
                id_contrato_alocacao=r[1],
                mes_referencia=r[2], 
                valor_esperado=r[3], 
                valor_pago=r[4], 
                status=r[5], 
                data_pagamento=r[6]
            )
            for r in rows
        ]