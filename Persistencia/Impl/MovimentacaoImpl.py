from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import Movimentacao

class MovimentacaoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, mov: Movimentacao) -> int:
        # Se tem ID, atualiza. Se não, cria.
        if mov.id_movimentacao:
            self.atualizar(mov)
            return mov.id_movimentacao
        else:
            sql = """
                INSERT INTO movimentacao (
                    descricao, valor, data_movimento, id_categoria, banco, forma_pagamento, 
                    id_veiculo, id_kitnet, identificador_bloco, 
                    id_pagamento_aluguel, id_divida_veiculo, id_pagamento_alocacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                mov.descricao, mov.valor, mov.data_movimento, mov.id_categoria, mov.banco, mov.forma_pagamento,
                mov.id_veiculo, mov.id_kitnet, mov.identificador_bloco,
                mov.id_pagamento_aluguel, mov.id_divida_veiculo, mov.id_pagamento_alocacao
            )
            id_gerado = self.__bd.executar(sql, params)
            mov.id_movimentacao = id_gerado
            return id_gerado

    def atualizar(self, mov: Movimentacao):
        sql = """
            UPDATE movimentacao 
            SET descricao=?, valor=?, data_movimento=?, id_categoria=?, banco=?, forma_pagamento=? 
            WHERE id_movimentacao=?
        """
        self.__bd.executar(sql, (
            mov.descricao, mov.valor, mov.data_movimento, mov.id_categoria, 
            mov.banco, mov.forma_pagamento, mov.id_movimentacao
        ))

    def deletar(self, id_movimentacao: int):
        self.__bd.executar("DELETE FROM movimentacao WHERE id_movimentacao=?", (id_movimentacao,))

    def buscar_por_id(self, id_mov: int) -> Optional[Movimentacao]:
        sql = """
            SELECT id_movimentacao, descricao, valor, data_movimento, id_categoria, banco, forma_pagamento,
                   id_veiculo, id_kitnet, identificador_bloco, 
                   id_pagamento_aluguel, id_divida_veiculo, id_pagamento_alocacao
            FROM movimentacao WHERE id_movimentacao=?
        """
        row = self.__bd.executar_query(sql, (id_mov,), fetchone=True)
        if row:
            return Movimentacao(
                id_movimentacao=row[0], 
                descricao=row[1], 
                valor=row[2], 
                data_movimento=row[3],
                id_categoria=row[4], 
                banco=row[5], 
                forma_pagamento=row[6],
                id_veiculo=row[7], 
                id_kitnet=row[8], 
                identificador_bloco=row[9],
                id_pagamento_aluguel=row[10], 
                id_divida_veiculo=row[11], 
                id_pagamento_alocacao=row[12]
            )
        return None

    def listar_periodo(self, data_inicio: str, data_fim: str) -> List[Movimentacao]:
        sql = """
            SELECT id_movimentacao, descricao, valor, data_movimento, id_categoria, banco, forma_pagamento,
                   id_veiculo, id_kitnet, identificador_bloco,
                   id_pagamento_aluguel, id_divida_veiculo, id_pagamento_alocacao
            FROM movimentacao 
            WHERE date(data_movimento) >= date(?) 
              AND date(data_movimento) <= date(?)
            ORDER BY data_movimento DESC
        """
        rows = self.__bd.executar_query(sql, (data_inicio, data_fim))
        
        lista = []
        for row in rows:
            m = Movimentacao(
                id_movimentacao=row[0], 
                descricao=row[1], 
                valor=row[2], 
                data_movimento=row[3],
                id_categoria=row[4], 
                banco=row[5], 
                forma_pagamento=row[6],
                id_veiculo=row[7], 
                id_kitnet=row[8], 
                identificador_bloco=row[9], 
                id_pagamento_aluguel=row[10], 
                id_divida_veiculo=row[11], 
                id_pagamento_alocacao=row[12]
            )
            lista.append(m)
        return lista