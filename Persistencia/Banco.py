import sqlite3

class BancoDeDados:
    def __init__(self, nome_bd="financas.db"):
        self.nome_bd = nome_bd

    def conectar(self):
        """Estabelece conexão com o banco de dados"""
        return sqlite3.connect(self.nome_bd)

    def criarBanco(self):
        """Cria todas as tabelas necessárias para o sistema"""
        try:
            con = self.conectar()
            cursor = con.cursor()

            # ===================================================
            # 1. MÓDULO IMOBILIÁRIO (KITNETS)
            # ===================================================
            
            # Tabela Kitnet
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kitnet (
                    id_kitnet INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero INTEGER,
                    quartos INTEGER DEFAULT 1,
                    preco_padrao REAL,
                    status TEXT NOT NULL
                );
            """)

            # Tabela Inquilino
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inquilino (
                    id_inquilino INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cpf TEXT,
                    estado_civil TEXT,
                    telefone TEXT,
                    sexo TEXT
                );
            """)

            # Tabela Contrato Kitnet (Arrumei os INTERGER e FKs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contrato_kitnet (
                    id_contrato_kitnet INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_kitnet INTEGER NOT NULL,
                    id_inquilino INTEGER NOT NULL,
                    valor_fechado REAL,
                    data_vencimento INTEGER NOT NULL, -- Dia do vencimento (ex: 10)
                    data_inicio TEXT NOT NULL,
                    data_fim TEXT,
                    ativo INTEGER DEFAULT 1, -- 1 para Sim, 0 para Não
                    mobiliado INTEGER DEFAULT 0,
                    obs_mobiliado TEXT,
                    pdf_caminho_contrato_kit TEXT,
                    FOREIGN KEY (id_kitnet) REFERENCES kitnet(id_kitnet),
                    FOREIGN KEY (id_inquilino) REFERENCES inquilino(id_inquilino)
                );
            """)

            # Tabela Pagamento Aluguel (Arrumei a FK e o CHECK)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagamento_aluguel (
                    id_aluguel INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_contrato_kitnet INTEGER NOT NULL,
                    mes_referencia TEXT,
                    valor_pago REAL DEFAULT 0.0,
                    data_pagamento TEXT,
                    status TEXT CHECK(status IN ('pendente', 'pago', 'atrasado')),
                    FOREIGN KEY (id_contrato_kitnet) REFERENCES contrato_kitnet(id_contrato_kitnet)
                );
            """)

            # ===================================================
            # 2. MÓDULO TRANSPORTE (VEÍCULOS)
            # ===================================================

            # Tabela Veículos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS veiculo (
                    id_veiculo INTEGER PRIMARY KEY AUTOINCREMENT,
                    modelo TEXT NOT NULL,
                    placa TEXT,
                    ano INTEGER,
                    finalidade TEXT CHECK(finalidade IN ('trabalho', 'projeto', 'revenda')),
                    status TEXT      CHECK(status IN ('ativo', 'oficina', 'vendido'))
                );
            """)

            # Tabela Dívidas Veículo (IPVA, Multas, etc)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS divida_veiculo (
                    id_divida INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_veiculo INTEGER NOT NULL,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_vencimento TEXT,
                    status TEXT DEFAULT 'pendente',
                    FOREIGN KEY (id_veiculo) REFERENCES veiculo(id_veiculo)
                );
            """)

            # Tabela Empresas (Clientes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresa (
                    id_empresa INTEGER PRIMARY KEY AUTOINCREMENT,
                    razao_social TEXT NOT NULL,
                    cnpj TEXT,
                    telefone TEXT
                );
            """)

            # Tabela Contrato Alocação (Transporte)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contrato_alocacao (
                    id_contrato_alocacao INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_empresa INTEGER NOT NULL,
                    id_veiculo INTEGER NOT NULL,
                    valor_mensal REAL NOT NULL,
                    dia_vencimento INTEGER,
                    ativo INTEGER DEFAULT 1,
                    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa),
                    FOREIGN KEY (id_veiculo) REFERENCES veiculo(id_veiculo)
                );
            """)

            # Tabela Pagamento Alocação
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagamento_alocacao (
                    id_pagamento_alocacao INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_contrato_alocacao INTEGER NOT NULL,
                    mes_referencia TEXT,
                    valor_esperado REAL,
                    status TEXT CHECK(status IN ('pendente', 'pago', 'atrasado')),
                    data_pagamento TEXT,
                    FOREIGN KEY (id_contrato_alocacao) REFERENCES contrato_alocacao(id_contrato_alocacao)
                );
            """)

            # ===================================================
            # 3. MÓDULO FINANCEIRO (CORE)
            # ===================================================

            # Tabela Categorias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categoria (
                    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    tipo TEXT CHECK(tipo IN ('receita', 'despesa'))
                );
            """)

            # Tabela Movimentações (O Extrato Geral)
            # Aqui juntamos tudo com FKs opcionais (podem ser NULL)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentacao (
                    id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL, -- Positivo ou Negativo
                    data_movimento TEXT NOT NULL,
                    id_categoria INTEGER NOT NULL,
                    
                    -- FKs Opcionais (Vínculos)
                    id_veiculo INTEGER, 
                    id_pagamento_aluguel INTEGER,
                    id_pagamento_alocacao INTEGER,
                    id_divida_veiculo INTEGER,

                    FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria),
                    FOREIGN KEY (id_veiculo) REFERENCES veiculo(id_veiculo),
                    FOREIGN KEY (id_pagamento_aluguel) REFERENCES pagamento_aluguel(id_aluguel),
                    FOREIGN KEY (id_pagamento_alocacao) REFERENCES pagamento_alocacao(id_pagamento_alocacao),
                    FOREIGN KEY (id_divida_veiculo) REFERENCES divida_veiculo(id_divida)
                );
            """)

            con.commit()
            print("Banco de dados atualizado com sucesso!")
            
        except sqlite3.Error as erro:
            print("Erro ao criar o banco:", erro)
            raise
        finally:
            con.close()


    def executar(self, sql, parametros=()):
        """Executa uma query que não retorna resultados (INSERT, UPDATE, DELETE)"""
        try:
            con = self.conectar()
            cursor = con.cursor()
            cursor.execute(sql, parametros)
            con.commit()
            return cursor.lastrowid
        except sqlite3.Error as erro:
            print("Erro ao executar SQL:", erro)
            raise
        finally:
            con.close()

    def executar_query(self, sql, parametros=(), fetchone=False):
        """Executa uma query que retorna resultados (SELECT)"""
        try:
            con = self.conectar()
            cursor = con.cursor()
            cursor.execute(sql, parametros)
            return cursor.fetchone() if fetchone else cursor.fetchall()
        except sqlite3.Error as erro:
            print("Erro ao consultar o banco de dados:", erro)
            raise
        finally:
            con.close()
    
    def executar_multiplos(self, comandos):
        """Executa múltiplos comandos SQL em uma única transação"""
        try:
            con = self.conectar()
            cursor = con.cursor()
            con.execute("BEGIN")
            for sql, params in comandos:
                cursor.execute(sql, params)
            con.commit()
        except sqlite3.Error as erro:
            con.rollback()
            print("Erro ao executar múltiplos comandos:", erro)
            raise
        finally:
            con.close()
