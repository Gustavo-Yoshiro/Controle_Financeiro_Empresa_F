from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.PagamentoAluguel import PagamentoAluguel

class PagamentoAluguelImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, pag: PagamentoAluguel) -> int:
        sql = """
            INSERT INTO pagamento_aluguel (id_contrato_kitnet, mes_referencia, valor_pago, data_pagamento, status) 
            VALUES (?, ?, ?, ?, ?)
        """
        parametros = (
            pag.id_contrato_kitnet, 
            pag.mes_referencia, 
            pag.valor_pago, 
            pag.data_pagamento, 
            pag.status
        )
        id_gerado = self.__bd.executar(sql, parametros)
        pag.id_aluguel = id_gerado
        return id_gerado

    def atualizar(self, pag: PagamentoAluguel) -> None:
        sql = """
            UPDATE pagamento_aluguel 
            SET id_contrato_kitnet=?, mes_referencia=?, valor_pago=?, data_pagamento=?, status=? 
            WHERE id_aluguel=?
        """
        parametros = (
            pag.id_contrato_kitnet, 
            pag.mes_referencia, 
            pag.valor_pago, 
            pag.data_pagamento, 
            pag.status, 
            pag.id_aluguel
        )
        self.__bd.executar(sql, parametros)

    def buscar_pendencias(self) -> List[PagamentoAluguel]:
        """
        Retorna tudo que não está pago (útil para alertas)
        """
        sql = """
            SELECT id_aluguel, id_contrato_kitnet, mes_referencia, valor_pago, data_pagamento, status 
            FROM pagamento_aluguel 
            WHERE status IN ('pendente', 'atrasado')
        """
        rows = self.__bd.executar_query(sql)
        
        return [
            PagamentoAluguel(
                id_aluguel=r[0], id_contrato_kitnet=r[1], mes_referencia=r[2], 
                valor_pago=r[3], data_pagamento=r[4], status=r[5]
            ) for r in rows
        ]
    
    def buscar_por_id(self, id_aluguel: int) -> Optional[PagamentoAluguel]:
        sql = "SELECT id_aluguel, id_contrato_kitnet, mes_referencia, valor_pago, data_pagamento, status FROM pagamento_aluguel WHERE id_aluguel = ?"
        row = self.__bd.executar_query(sql, (id_aluguel,), fetchone=True)
        
        if row:
            return PagamentoAluguel(
                id_aluguel=row[0],
                id_contrato_kitnet=row[1],
                mes_referencia=row[2],
                valor_pago=row[3],
                data_pagamento=row[4],
                status=row[5]
            )
        return None