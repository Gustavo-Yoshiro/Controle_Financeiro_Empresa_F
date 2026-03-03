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
                INSERT INTO pagamento_aluguel 
                (id_contrato_kitnet, mes_referencia, valor_esperado, valor_pago, data_pagamento, status, obs)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            parametros = (
                pag.id_contrato_kitnet, 
                pag.mes_referencia, 
                pag.valor_esperado, 
                pag.valor_pago, 
                pag.data_pagamento, 
                pag.status,
                pag.obs             
            )
            id_gerado = self.__bd.executar(sql, parametros)
            pag.id_aluguel = id_gerado
            return id_gerado

    def atualizar(self, pag: PagamentoAluguel):
        
        sql = """
            UPDATE pagamento_aluguel 
            SET id_contrato_kitnet=?, mes_referencia=?, valor_esperado=?, 
                valor_pago=?, data_pagamento=?, status=?, obs=? 
            WHERE id_aluguel=?
        """
        parametros = (
            
            pag.id_contrato_kitnet, 
            pag.mes_referencia, 
            pag.valor_esperado, 
            pag.valor_pago, 
            pag.data_pagamento, 
            pag.status, 
            pag.obs,   
            pag.id_aluguel
        )
        self.__bd.executar(sql, parametros)

    def deletar(self, id_aluguel: int) -> None:
        sql = "DELETE FROM pagamento_aluguel WHERE id_aluguel = ?"
        self.__bd.executar(sql, (id_aluguel,))

    def buscar_por_id(self, id_pagamento: int) -> Optional[PagamentoAluguel]:
        sql = """
            SELECT id_aluguel, id_contrato_kitnet, mes_referencia, valor_esperado, 
                   valor_pago, data_pagamento, status, obs 
            FROM pagamento_aluguel WHERE id_aluguel = ?
        """
        row = self.__bd.executar_query(sql, (id_pagamento,), fetchone=True)
        if row:
            return PagamentoAluguel(
                id_aluguel=row[0], 
                id_contrato_kitnet=row[1], 
                mes_referencia=row[2], 
                valor_esperado=row[3], 
                valor_pago=row[4], 
                data_pagamento=row[5], 
                status=row[6],
                obs=row[7]           
            )
        return None

    def listar_pendentes(self) -> List[PagamentoAluguel]:
        """ 
        Retorna o que não foi pago (pendente) OU foi pago parcialmente (parcial)
        para preencher o Selectbox de recebimento.
        """
        sql = """
            SELECT id_aluguel, id_contrato_kitnet, mes_referencia, valor_esperado, 
                   valor_pago, data_pagamento, status, obs 
            FROM pagamento_aluguel 
            WHERE status IN ('pendente', 'parcial') 
            ORDER BY mes_referencia ASC
        """
        rows = self.__bd.executar_query(sql)
        
        return [
            PagamentoAluguel(
                id_aluguel=r[0], 
                id_contrato_kitnet=r[1], 
                mes_referencia=r[2], 
                valor_esperado=r[3], 
                valor_pago=r[4], 
                data_pagamento=r[5], 
                status=r[6],
                obs=r[7]
            ) for r in rows
        ]

    def listar_todos(self) -> List[PagamentoAluguel]:
        sql = """
            SELECT id_aluguel, id_contrato_kitnet, mes_referencia, valor_esperado, 
                   valor_pago, data_pagamento, status, obs 
            FROM pagamento_aluguel
            ORDER BY mes_referencia DESC
        """
        rows = self.__bd.executar_query(sql)
        return [
            PagamentoAluguel(
                id_aluguel=r[0], 
                id_contrato_kitnet=r[1], 
                mes_referencia=r[2], 
                valor_esperado=r[3], 
                valor_pago=r[4], 
                data_pagamento=r[5], 
                status=r[6],
                obs=r[7]
            ) for r in rows
        ]