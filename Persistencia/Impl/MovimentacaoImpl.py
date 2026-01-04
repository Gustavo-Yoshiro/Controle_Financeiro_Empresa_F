from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.Movimentacao import Movimentacao 

class MovimentacaoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, mov: Movimentacao) -> int:
        sql = """INSERT INTO movimentacao (descricao, valor, data_movimento, id_categoria, 
                 id_veiculo, id_pagamento_aluguel, id_pagamento_alocacao, id_divida_veiculo) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        parametros = (
            mov.descricao, mov.valor, mov.data_movimento, mov.id_categoria,
            mov.id_veiculo, mov.id_pagamento_aluguel, mov.id_pagamento_alocacao, mov.id_divida_veiculo
        )
        id_gerado = self.__bd.executar(sql, parametros)
        mov.id_movimentacao = id_gerado
        return id_gerado

    def atualizar(self, mov: Movimentacao) -> None:
        sql = """UPDATE movimentacao SET descricao=?, valor=?, data_movimento=?, id_categoria=?, 
                 id_veiculo=?, id_pagamento_aluguel=?, id_pagamento_alocacao=?, id_divida_veiculo=? 
                 WHERE id_movimentacao=?"""
        parametros = (
            mov.descricao, mov.valor, mov.data_movimento, mov.id_categoria,
            mov.id_veiculo, mov.id_pagamento_aluguel, mov.id_pagamento_alocacao, mov.id_divida_veiculo,
            mov.id_movimentacao
        )
        self.__bd.executar(sql, parametros)

    def deletar(self, id_movimentacao: int) -> None:
        sql = "DELETE FROM movimentacao WHERE id_movimentacao = ?"
        self.__bd.executar(sql, (id_movimentacao,))

    def buscar_por_id(self, id_movimentacao: int) -> Optional[Movimentacao]:
        sql = """SELECT id_movimentacao, descricao, valor, data_movimento, id_categoria, 
                 id_veiculo, id_pagamento_aluguel, id_pagamento_alocacao, id_divida_veiculo 
                 FROM movimentacao WHERE id_movimentacao = ?"""
        row = self.__bd.executar_query(sql, (id_movimentacao,), fetchone=True)
        if row:
            return Movimentacao(
                id_movimentacao=row[0], descricao=row[1], valor=row[2], data_movimento=row[3], 
                id_categoria=row[4], id_veiculo=row[5], id_pagamento_aluguel=row[6], 
                id_pagamento_alocacao=row[7], id_divida_veiculo=row[8]
            )
        return None

    def listar_tudo(self) -> List[Movimentacao]:
        sql = """SELECT id_movimentacao, descricao, valor, data_movimento, id_categoria, 
                 id_veiculo, id_pagamento_aluguel, id_pagamento_alocacao, id_divida_veiculo 
                 FROM movimentacao"""
        rows = self.__bd.executar_query(sql)
        return [Movimentacao(
                id_movimentacao=r[0], descricao=r[1], valor=r[2], data_movimento=r[3], 
                id_categoria=r[4], id_veiculo=r[5], id_pagamento_aluguel=r[6], 
                id_pagamento_alocacao=r[7], id_divida_veiculo=r[8]
            ) for r in rows]