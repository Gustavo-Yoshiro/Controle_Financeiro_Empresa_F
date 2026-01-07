from Persistencia.Banco import BancoDeDados

class PopulacaoInicial:
    def __init__(self):
        self.bd = BancoDeDados()

    def popular_categorias_padrao(self):
        """
        Insere as categorias fundamentais com IDs FIXOS.
        Usa 'INSERT OR IGNORE' para não duplicar se já existir.
        """
        # Lista: (ID_FIXO, NOME, TIPO)
        categorias_fixas = [
            # --- GERAIS ---
            (1, "Receita Geral", "receita"),         # Fallback padrão
            (2, "Despesa Geral", "despesa"),         # Fallback padrão
            
            # --- IMÓVEIS (KITNETS) ---
            (3, "Aluguel de Imóveis", "receita"),    # ID usado no LocacaoService
            (4, "Manutenção de Imóvel", "despesa"),  # Contas de água/luz/reparo
            
            # --- FROTA (LOGÍSTICA) ---
            (5, "Receita de Logística", "receita"),  # ID usado no LogisticaService
            (6, "Manutenção de Veículo", "despesa"), # Gasolina, mecânica
            
            # --- FINANCEIRO ---
            (7, "Entrada de Empréstimo", "receita"), # Quando você pega dinheiro
            (8, "Pagamento de Dívida", "despesa"),   # Quando paga boleto ou parcela
            (9, "Renda Extra", "receita"),
            (10, "Alimentação", "despesa"),
            (11, "Lazer", "despesa")
        ]

        # SQL SQLite (INSERT OR IGNORE mantem o ID se já existir, senão cria)
        sql = "INSERT OR IGNORE INTO categoria (id_categoria, nome, tipo) VALUES (?, ?, ?)"

        alteracoes = 0
        for cat in categorias_fixas:
            try:
                # cat[0]=id, cat[1]=nome, cat[2]=tipo
                self.bd.executar(sql, (cat[0], cat[1], cat[2]))
                alteracoes += 1
            except Exception as e:
                print(f"Erro ao popular categoria ID {cat[0]}: {e}")

        if alteracoes > 0:
            print(f"✅ População Inicial: Categorias padrão verificadas/inseridas.")