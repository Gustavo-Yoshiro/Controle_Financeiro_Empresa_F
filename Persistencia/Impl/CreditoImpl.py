from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import CartaoCredito

class CartaoCreditoImpl:
    def __init__(self):
        self.db = BancoDeDados()

    def salvar(self, cartao: CartaoCredito):
        # Tenta inserir um novo cartão
        sql = """
            INSERT INTO cartao_credito (nome, dia_fechamento, dia_vencimento, limite, bandeira) 
            VALUES (?, ?, ?, ?, ?)
        """
        params = (cartao.nome, cartao.dia_fechamento, cartao.dia_vencimento, cartao.limite, cartao.bandeira)
        
        try:
            return self.db.executar(sql, params)
        except Exception as e:
            print(f"Erro ao salvar cartão: {e}")
            return None

    def listar_todos(self):
        sql = "SELECT id_cartao, nome, dia_fechamento, dia_vencimento, limite, bandeira FROM cartao_credito"
        rows = self.db.executar_query(sql)
        lista = []
        for r in rows:
            c = CartaoCredito(
                id_cartao=r[0],
                nome=r[1],
                dia_fechamento=r[2],
                dia_vencimento=r[3],
                limite=r[4],
                bandeira=r[5]
            )
            lista.append(c)
        return lista
    
    def buscar_por_nome(self, nome: str):
        sql = "SELECT id_cartao, nome, dia_fechamento, dia_vencimento, limite, bandeira FROM cartao_credito WHERE nome = ?"
        r = self.db.executar_query(sql, (nome,), fetchone=True)
        if r:
            return CartaoCredito(
                id_cartao=r[0], nome=r[1], dia_fechamento=r[2], 
                dia_vencimento=r[3], limite=r[4], bandeira=r[5]
            )
        return None

    def buscar_por_id(self, id_cartao: int):
        sql = "SELECT id_cartao, nome, dia_fechamento, dia_vencimento, limite, bandeira FROM cartao_credito WHERE id_cartao = ?"
        r = self.db.executar_query(sql, (id_cartao,), fetchone=True)
        if r:
            return CartaoCredito(
                id_cartao=r[0], nome=r[1], dia_fechamento=r[2], 
                dia_vencimento=r[3], limite=r[4], bandeira=r[5]
            )
        return None

    def atualizar(self, cartao: CartaoCredito):
        sql = """
            UPDATE cartao_credito 
            SET nome=?, dia_fechamento=?, dia_vencimento=?, limite=?, bandeira=?
            WHERE id_cartao=?
        """
        params = (cartao.nome, cartao.dia_fechamento, cartao.dia_vencimento, cartao.limite, cartao.bandeira, cartao.id_cartao)
        self.db.executar(sql, params)

    def deletar(self, id_cartao: int):
        sql = "DELETE FROM cartao_credito WHERE id_cartao=?"
        self.db.executar(sql, (id_cartao,))