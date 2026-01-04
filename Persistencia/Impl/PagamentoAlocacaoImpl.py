from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.PagamentoAlocacao import PagamentoAlocacao

class PagamentoAlocacaoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, pag: PagamentoAlocacao) -> int:
        """
        Gera uma nova cobrança/fatura para a empresa.
        """
        sql = """
            INSERT INTO pagamento_alocacao (id_contrato_alocacao, mes_referencia, valor_esperado, status, data_pagamento) 
            VALUES (?, ?, ?, ?, ?)
        """
        parametros = (
            pag.id_contrato_alocacao,
            pag.mes_referencia,
            pag.valor_esperado,
            pag.status,
            pag.data_pagamento
        )
        id_gerado = self.__bd.executar(sql, parametros)
        pag.id_pagamento_alocacao = id_gerado
        return id_gerado

    def atualizar(self, pag: PagamentoAlocacao) -> None:
        """
        Atualiza o status (ex: de Pendente para Pago) ou corrige valores.
        """
        sql = """
            UPDATE pagamento_alocacao 
            SET id_contrato_alocacao=?, mes_referencia=?, valor_esperado=?, status=?, data_pagamento=? 
            WHERE id_pagamento_alocacao=?
        """
        parametros = (
            pag.id_contrato_alocacao,
            pag.mes_referencia,
            pag.valor_esperado,
            pag.status,
            pag.data_pagamento,
            pag.id_pagamento_alocacao
        )
        self.__bd.executar(sql, parametros)
        
    def deletar(self, id_pagamento: int) -> None:
        sql = "DELETE FROM pagamento_alocacao WHERE id_pagamento_alocacao = ?"
        self.__bd.executar(sql, (id_pagamento,))

    def buscar_por_id(self, id_pagamento: int) -> Optional[PagamentoAlocacao]:
        sql = """
            SELECT id_pagamento_alocacao, id_contrato_alocacao, mes_referencia, valor_esperado, status, data_pagamento 
            FROM pagamento_alocacao WHERE id_pagamento_alocacao = ?
        """
        row = self.__bd.executar_query(sql, (id_pagamento,), fetchone=True)
        if row:
            return PagamentoAlocacao(
                id_pagamento_alocacao=row[0], id_contrato_alocacao=row[1], mes_referencia=row[2], 
                valor_esperado=row[3], status=row[4], data_pagamento=row[5]
            )
        return None

    def listar_pendentes(self) -> List[PagamentoAlocacao]:
        """
        Lista todas as faturas que a empresa ainda não pagou.
        """
        sql = """
            SELECT id_pagamento_alocacao, id_contrato_alocacao, mes_referencia, valor_esperado, status, data_pagamento 
            FROM pagamento_alocacao WHERE status IN ('pendente', 'atrasado')
        """
        rows = self.__bd.executar_query(sql)
        return [
            PagamentoAlocacao(
                id_pagamento_alocacao=r[0], id_contrato_alocacao=r[1], mes_referencia=r[2], 
                valor_esperado=r[3], status=r[4], data_pagamento=r[5]
            ) for r in rows
        ]