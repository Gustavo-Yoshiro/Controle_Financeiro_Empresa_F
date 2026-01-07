from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import PagamentoAluguel

class PagamentoAluguelImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, pag: PagamentoAluguel) -> int:
        # PADRÃO INTELIGENTE: Se tem ID, atualiza. Se não, cria.
        if pag.id_aluguel:
            self.atualizar(pag)
            return pag.id_aluguel
        else:
            sql = """
                INSERT INTO pagamento_aluguel (id_contrato_kitnet, mes_referencia, valor_pago, data_pagamento, status)
                VALUES (?, ?, ?, ?, ?)
            """
            id_gerado = self.__bd.executar(sql, (
                pag.id_contrato_kitnet, 
                pag.mes_referencia, 
                pag.valor_pago, 
                pag.data_pagamento, 
                pag.status
            ))
            pag.id_aluguel = id_gerado
            return id_gerado

    def atualizar(self, pag: PagamentoAluguel):
        sql = """
            UPDATE pagamento_aluguel 
            SET id_contrato_kitnet=?, mes_referencia=?, valor_pago=?, data_pagamento=?, status=? 
            WHERE id_aluguel=?
        """
        self.__bd.executar(sql, (
            pag.id_contrato_kitnet, 
            pag.mes_referencia, 
            pag.valor_pago, 
            pag.data_pagamento, 
            pag.status, 
            pag.id_aluguel
        ))

    def deletar(self, id_aluguel: int) -> None:
        sql = "DELETE FROM pagamento_aluguel WHERE id_aluguel = ?"
        self.__bd.executar(sql, (id_aluguel,))

    def buscar_por_id(self, id_pagamento: int) -> Optional[PagamentoAluguel]:
        sql = """
            SELECT id_aluguel, id_contrato_kitnet, mes_referencia, valor_pago, data_pagamento, status 
            FROM pagamento_aluguel WHERE id_aluguel = ?
        """
        row = self.__bd.executar_query(sql, (id_pagamento,), fetchone=True)
        if row:
            return PagamentoAluguel(
                id_aluguel=row[0], id_contrato_kitnet=row[1], mes_referencia=row[2], 
                valor_pago=row[3], data_pagamento=row[4], status=row[5]
            )
        return None

    def listar_pendentes(self) -> List[PagamentoAluguel]:
        """ Retorna apenas o que ainda não foi pago para preencher o Selectbox """
        sql = """
            SELECT id_aluguel, id_contrato_kitnet, mes_referencia, valor_pago, data_pagamento, status 
            FROM pagamento_aluguel WHERE status = 'pendente'
        """
        rows = self.__bd.executar_query(sql)
        
        return [
            PagamentoAluguel(
                id_aluguel=r[0], id_contrato_kitnet=r[1], mes_referencia=r[2], 
                valor_pago=r[3], data_pagamento=r[4], status=r[5]
            ) for r in rows
        ]

    def listar_todos(self) -> List[PagamentoAluguel]:
        sql = "SELECT id_aluguel, id_contrato_kitnet, mes_referencia, valor_pago, data_pagamento, status FROM pagamento_aluguel"
        rows = self.__bd.executar_query(sql)
        return [
            PagamentoAluguel(
                id_aluguel=r[0], id_contrato_kitnet=r[1], mes_referencia=r[2], 
                valor_pago=r[3], data_pagamento=r[4], status=r[5]
            ) for r in rows
        ]