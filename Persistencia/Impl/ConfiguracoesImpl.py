from typing import List, Dict, Optional
from Persistencia.Banco import BancoDeDados

class ConfiguracaoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    # =========================================================================
    # BANCOS
    # =========================================================================
    def listar_bancos(self) -> List[str]:
        rows = self.__bd.executar_query("SELECT nome FROM aux_banco ORDER BY nome")
        return [r[0] for r in rows]

    def adicionar_banco(self, nome: str):
        self.__bd.executar("INSERT INTO aux_banco (nome) VALUES (?)", (nome,))

    def atualizar_banco(self, nome_antigo: str, novo_nome: str):
        # Atualiza a lista auxiliar
        self.__bd.executar("UPDATE aux_banco SET nome=? WHERE nome=?", (novo_nome, nome_antigo))
        # Atualiza o histórico para não quebrar relatórios antigos
        self.__bd.executar("UPDATE movimentacao SET banco=? WHERE banco=?", (novo_nome, nome_antigo))

    def deletar_banco(self, nome: str):
        self.__bd.executar("DELETE FROM aux_banco WHERE nome=?", (nome,))

    def banco_esta_em_uso(self, nome: str) -> bool:
        # Retorna True se tiver alguma transação usando esse banco
        sql = "SELECT count(*) FROM movimentacao WHERE banco=?"
        row = self.__bd.executar_query(sql, (nome,), fetchone=True)
        return row[0] > 0

    # =========================================================================
    # FORMAS DE PAGAMENTO
    # =========================================================================
    def listar_formas(self) -> List[str]:
        rows = self.__bd.executar_query("SELECT nome FROM aux_forma_pagamento ORDER BY nome")
        return [r[0] for r in rows]

    def adicionar_forma(self, nome: str):
        self.__bd.executar("INSERT INTO aux_forma_pagamento (nome) VALUES (?)", (nome,))

    def atualizar_forma(self, nome_antigo: str, novo_nome: str):
        self.__bd.executar("UPDATE aux_forma_pagamento SET nome=? WHERE nome=?", (novo_nome, nome_antigo))
        self.__bd.executar("UPDATE movimentacao SET forma_pagamento=? WHERE forma_pagamento=?", (novo_nome, nome_antigo))

    def deletar_forma(self, nome: str):
        self.__bd.executar("DELETE FROM aux_forma_pagamento WHERE nome=?", (nome,))

    def forma_esta_em_uso(self, nome: str) -> bool:
        sql = "SELECT count(*) FROM movimentacao WHERE forma_pagamento=?"
        row = self.__bd.executar_query(sql, (nome,), fetchone=True)
        return row[0] > 0

    # =========================================================================
    # CATEGORIAS
    # =========================================================================
    def listar_categorias(self) -> List[Dict]:
        rows = self.__bd.executar_query("SELECT id_categoria, nome, tipo FROM categoria ORDER BY nome")
        return [{"id": r[0], "nome": r[1], "tipo": r[2]} for r in rows]

    def adicionar_categoria(self, nome: str, tipo: str):
        self.__bd.executar("INSERT INTO categoria (nome, tipo) VALUES (?, ?)", (nome, tipo))

    def atualizar_categoria(self, id_cat: int, novo_nome: str):
        self.__bd.executar("UPDATE categoria SET nome=? WHERE id_categoria=?", (novo_nome, id_cat))

    def deletar_categoria(self, id_cat: int):
        self.__bd.executar("DELETE FROM categoria WHERE id_categoria=?", (id_cat,))

    def categoria_esta_em_uso(self, id_cat: int) -> bool:
        sql = "SELECT count(*) FROM movimentacao WHERE id_categoria=?"
        row = self.__bd.executar_query(sql, (id_cat,), fetchone=True)
        return row[0] > 0