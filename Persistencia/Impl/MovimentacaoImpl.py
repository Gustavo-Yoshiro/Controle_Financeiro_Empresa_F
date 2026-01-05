from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.Movimentacao import Movimentacao

class MovimentacaoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, mov: Movimentacao) -> int:
        if mov.id_movimentacao:
            # ==========================================================
            # UPDATE (Edição)
            # ==========================================================
            # Atualiza os dados financeiros e de classificação
            sql = """
                UPDATE movimentacao 
                SET descricao=?, valor=?, data_movimento=?, id_categoria=?, 
                    banco=?, forma_pagamento=? 
                WHERE id_movimentacao=?
            """
            params = (
                mov.descricao, 
                mov.valor, 
                mov.data_movimento, 
                mov.id_categoria, 
                mov.banco, 
                mov.forma_pagamento, 
                mov.id_movimentacao
            )
            self.__bd.executar(sql, params)
        else:
            # ==========================================================
            # INSERT (Novo Lançamento)
            # ==========================================================
            # Insere tudo, inclusive os vínculos (id_veiculo, id_aluguel, etc)
            sql = """
                INSERT INTO movimentacao (
                    descricao, valor, data_movimento, id_categoria, 
                    banco, forma_pagamento, 
                    id_veiculo, id_pagamento_aluguel, id_pagamento_alocacao, id_divida_veiculo
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                mov.descricao, 
                mov.valor, 
                mov.data_movimento, 
                mov.id_categoria, 
                mov.banco, 
                mov.forma_pagamento,
                # Campos Opcionais (FKs)
                mov.id_veiculo, 
                mov.id_pagamento_aluguel, 
                mov.id_pagamento_alocacao, 
                mov.id_divida_veiculo
            )
            mov.id_movimentacao = self.__bd.executar(sql, params)
            
        return mov.id_movimentacao

    def excluir(self, id_movimentacao: int):
        """Remove uma movimentação do banco"""
        sql = "DELETE FROM movimentacao WHERE id_movimentacao=?"
        self.__bd.executar(sql, (id_movimentacao,))

    def buscar_por_id(self, id_movimentacao: int) -> Optional[Movimentacao]:
        """Busca um único registro para edição"""
        sql = """
            SELECT id_movimentacao, descricao, valor, data_movimento, id_categoria, 
                   banco, forma_pagamento, 
                   id_veiculo, id_pagamento_aluguel, id_pagamento_alocacao, id_divida_veiculo
            FROM movimentacao 
            WHERE id_movimentacao = ?
        """
        row = self.__bd.executar_query(sql, (id_movimentacao,), fetchone=True)
        
        if row:
            return Movimentacao(
                id_movimentacao=row[0],
                descricao=row[1],
                valor=row[2],
                data_movimento=row[3],
                id_categoria=row[4],
                banco=row[5] if row[5] else "Não Informado",
                forma_pagamento=row[6] if row[6] else "Outro",
                id_veiculo=row[7],
                id_pagamento_aluguel=row[8],
                id_pagamento_alocacao=row[9],
                id_divida_veiculo=row[10]
            )
        return None

    def listar_periodo(self, data_inicio: str, data_fim: str) -> List[Movimentacao]:
        """Lista para extrato e relatórios"""
        sql = """
            SELECT id_movimentacao, descricao, valor, data_movimento, id_categoria, 
                   banco, forma_pagamento,
                   id_veiculo, id_pagamento_aluguel, id_pagamento_alocacao, id_divida_veiculo
            FROM movimentacao 
            WHERE data_movimento BETWEEN ? AND ? 
            ORDER BY data_movimento DESC
        """
        rows = self.__bd.executar_query(sql, (data_inicio, data_fim))
        
        lista = []
        for r in rows:
            # Tratamento para dados antigos que podem vir NULL do banco
            banco_val = r[5] if r[5] else "Antigo"
            forma_val = r[6] if r[6] else "Outro"

            lista.append(Movimentacao(
                id_movimentacao=r[0],
                descricao=r[1],
                valor=r[2],
                data_movimento=r[3],
                id_categoria=r[4],
                banco=banco_val,
                forma_pagamento=forma_val,
                id_veiculo=r[7],
                id_pagamento_aluguel=r[8],
                id_pagamento_alocacao=r[9],
                id_divida_veiculo=r[10]
            ))
        return lista