from Persistencia.Banco import BancoDeDados

class PopulacaoInicial:
    def __init__(self):
        self.bd = BancoDeDados()

    def popular_tudo(self):
        print("🚀 Iniciando População Inicial...")
        self.popular_categorias_padrao()
        self.popular_bancos_padrao()
        self.popular_formas_pagamento()
        print("✅ Banco de dados atualizado com dados padrão!")

    def popular_categorias_padrao(self):
        # (Mantém a mesma lógica anterior para categorias, pois é tabela separada)
        categorias_fixas = [
            (1, "Receita Geral", "receita"),
            (2, "Despesa Geral", "despesa"),
            (3, "Aluguel de Imóveis", "receita"),
            (4, "Manutenção de Imóvel", "despesa"),
            (5, "Receita de Logística", "receita"),
            (6, "Manutenção de Veículo", "despesa"),
            (7, "Entrada de Empréstimo", "receita"),
            (8, "Pagamento de Dívida", "despesa"),
            (9, "Renda Extra", "receita"),
            (10, "Pagamento de Fatura", "despesa"), # <--- Importante para o Cartão
            (11, "Alimentação / Mercado", "despesa"),
            (12, "Lazer / Hobby", "despesa"),
            (13, "Transporte / Uber", "despesa"),
            (14, "Saúde", "despesa"),
            (15, "Educação", "despesa"),
            (16, "Assinaturas", "despesa"),
            (17, "Bares e Restaurantes", "despesa"),
            (18, "Casa", "despesa"),
            (19, "Vestuário", "despesa"),
            (20, "Investimentos", "despesa")
        ]
        sql = "INSERT OR IGNORE INTO categoria (id_categoria, nome, tipo) VALUES (?, ?, ?)"
        for cat in categorias_fixas:
            self.bd.executar(sql, cat)

    def popular_bancos_padrao(self):
        """
        Insere bancos na tabela 'aux_banco'.
        Como o campo 'nome' é UNIQUE, usamos INSERT OR IGNORE.
        """
        lista_bancos = [
            "Nubank", "Inter", "C6 Bank", "XP", "BTG Pactual",
            "Banco do Brasil", "Caixa", "Itaú", "Bradesco", "Santander",
            "Dinheiro", "Carteira" # Importante ter esses dois
        ]
        
        sql = "INSERT OR IGNORE INTO aux_banco (nome) VALUES (?)"
        
        for banco in lista_bancos:
            # Passamos como tupla (banco,)
            self.bd.executar(sql, (banco,))

    def popular_formas_pagamento(self):
        """
        Insere formas na tabela 'aux_forma_pagamento'.
        """
        lista_formas = [
            "Débito", 
            "Crédito",  # Essencial para a lógica de fatura
            "Pix", 
            "Dinheiro", 
            "Boleto", 
            "Transferência"
        ]
        
        sql = "INSERT OR IGNORE INTO aux_forma_pagamento (nome) VALUES (?)"
        
        for forma in lista_formas:
            self.bd.executar(sql, (forma,))