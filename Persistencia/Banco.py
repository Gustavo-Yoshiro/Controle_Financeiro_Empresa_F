import sqlite3
import os

class BancoDeDados:
    def __init__(self, nome_bd="financas.db"):
        self.nome_bd = nome_bd

    def conectar(self):
        con = sqlite3.connect(self.nome_bd)
        # ATIVA AS CHAVES ESTRANGEIRAS (CRUCIAL!)
        con.execute("PRAGMA foreign_keys = ON;")
        return con

    def criarBanco(self):
        try:
            con = self.conectar()
            cursor = con.cursor()

            # 1. CONFIGURAÇÃO
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aux_banco (
                    id_banco INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aux_forma_pagamento (
                    id_forma INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categoria (
                    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    tipo TEXT CHECK(tipo IN ('receita', 'despesa'))
                );
            """)

            # 2. KITNET
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kitnet (
                    id_kitnet INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero INTEGER,
                    quartos INTEGER DEFAULT 1,
                    preco_padrao REAL,
                    status TEXT NOT NULL,
                    identificador TEXT DEFAULT 'K'
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inquilino (
                    id_inquilino INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cpf TEXT,
                    telefone TEXT,
                    estado_civil TEXT,
                    profissao TEXT,
                    sexo TEXT,
                    email TEXT,
                    obs TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contrato_kitnet (
                    id_contrato_kitnet INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_kitnet INTEGER NOT NULL,
                    id_inquilino INTEGER NOT NULL,
                    valor_fechado REAL,
                    valor_esgoto_padrao REAL DEFAULT 0.0,
                    data_vencimento INTEGER NOT NULL, 
                    data_inicio TEXT NOT NULL,
                    data_fim TEXT,
                    ativo INTEGER DEFAULT 1,
                    mobiliado INTEGER DEFAULT 0,
                    obs_mobiliado TEXT,
                    pdf_caminho_contrato_kit TEXT,
                    FOREIGN KEY (id_kitnet) REFERENCES kitnet(id_kitnet),
                    FOREIGN KEY (id_inquilino) REFERENCES inquilino(id_inquilino)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagamento_aluguel (
                    id_aluguel INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_contrato_kitnet INTEGER NOT NULL,
                    mes_referencia TEXT,
                    valor_esperado REAL,
                    valor_pago REAL DEFAULT 0.0,
                    data_pagamento TEXT,
                    status TEXT CHECK(status IN ('pendente', 'pago', 'atrasado', 'parcial')),
                    obs TEXT,
                    FOREIGN KEY (id_contrato_kitnet) REFERENCES contrato_kitnet(id_contrato_kitnet)
                );
            """)

            # 3. VEÍCULO
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS veiculo (
                    id_veiculo INTEGER PRIMARY KEY AUTOINCREMENT,
                    modelo TEXT NOT NULL,
                    placa TEXT,
                    ano INTEGER,
                    finalidade TEXT,
                    status TEXT DEFAULT 'ativo'
                );
            """)
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresa (
                    id_empresa INTEGER PRIMARY KEY AUTOINCREMENT,
                    razao_social TEXT NOT NULL,
                    cnpj TEXT,
                    telefone TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contrato_alocacao (
                    id_contrato_alocacao INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_empresa INTEGER NOT NULL,
                    id_veiculo INTEGER NOT NULL,
                    valor_mensal REAL NOT NULL,
                    dia_vencimento INTEGER,
                    ativo INTEGER DEFAULT 1,
                    data_inicio TEXT, 
                    data_fim TEXT,    
                    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa),
                    FOREIGN KEY (id_veiculo) REFERENCES veiculo(id_veiculo)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagamento_alocacao (
                    id_pagamento_alocacao INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_contrato_alocacao INTEGER NOT NULL,
                    mes_referencia TEXT,
                    valor_esperado REAL,
                    valor_pago REAL DEFAULT 0.0, 
                    status TEXT CHECK(status IN ('pendente', 'pago', 'atrasado')),
                    data_pagamento TEXT,
                    FOREIGN KEY (id_contrato_alocacao) REFERENCES contrato_alocacao(id_contrato_alocacao)
                );
            """)

            # 4. OUTROS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emprestimo (
                    id_emprestimo INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT,
                    valor_total REAL,
                    valor_parcela REAL,
                    qtd_parcelas INTEGER,
                    juros_mensal REAL,
                    data_inicio TEXT,            -- Data que o dinheiro caiu
                    data_primeira_parcela TEXT,  -- <--- NOVO: Data que começa a pagar
                    banco_origem TEXT,
                    valor_pago REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'ativo'
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS boleto (
                    id_boleto INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT,
                    valor REAL,
                    data_vencimento TEXT,
                    codigo_barras TEXT,
                    id_categoria INTEGER,
                    status TEXT,
                    obs TEXT,
                    banco_pagamento TEXT,
                    banco_cartao TEXT  
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pix (
                    id_pix INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT,
                    chave TEXT,
                    tipo TEXT,
                    titular TEXT,
                    banco TEXT,
                    favorito INTEGER DEFAULT 0
                );
            """)

            # 5. MOVIMENTAÇÃO (CENTRAL) 
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentacao (
                    id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_movimento TEXT NOT NULL,
                    id_categoria INTEGER NOT NULL,
                    banco TEXT,
                    forma_pagamento TEXT,
                    
                    id_veiculo INTEGER, 
                    id_kitnet INTEGER,
                    identificador_bloco TEXT, -- <--- CAMPO NOVO ADICIONADO AQUI
                    id_pagamento_aluguel INTEGER,
                    id_divida_veiculo INTEGER,
                    id_pagamento_alocacao INTEGER,
                    
                    FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria),
                    FOREIGN KEY (id_veiculo) REFERENCES veiculo(id_veiculo),
                    FOREIGN KEY (id_kitnet) REFERENCES kitnet(id_kitnet),
                    FOREIGN KEY (id_pagamento_aluguel) REFERENCES pagamento_aluguel(id_aluguel),
                    FOREIGN KEY (id_divida_veiculo) REFERENCES divida_veiculo(id_divida),
                    FOREIGN KEY (id_pagamento_alocacao) REFERENCES pagamento_alocacao(id_pagamento_alocacao)
                );
            """)

            # 6. ÍNDICES (PERFORMANCE)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mov_data ON movimentacao(data_movimento);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mov_cat ON movimentacao(id_categoria);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mov_kit ON movimentacao(id_kitnet);")

            con.commit()
            print("Banco de dados criado com sucesso e FKs ativadas!")
            
        except sqlite3.Error as erro:
            print("Erro crítico ao criar o banco:", erro)
            raise
        finally:
            con.close()

    def executar(self, sql, params=()):
        con = self.conectar()
        cursor = con.cursor()
        try:
            cursor.execute(sql, params)
            id_gerado = cursor.lastrowid
            con.commit()
            return id_gerado
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def executar_query(self, sql, params=(), fetchone=False):
        con = self.conectar()
        cursor = con.cursor()
        try:
            cursor.execute(sql, params)
            res = cursor.fetchone() if fetchone else cursor.fetchall()
            return res
        finally:
            con.close()