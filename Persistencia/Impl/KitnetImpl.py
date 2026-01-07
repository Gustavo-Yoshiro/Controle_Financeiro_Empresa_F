from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import Kitnet

class KitnetImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, kitnet: Kitnet) -> int:
        # PADRÃO INTELIGENTE: Se tem ID, atualiza. Se não, cria.
        if kitnet.id_kitnet:
            sql = """
                UPDATE kitnet 
                SET numero=?, quartos=?, preco_padrao=?, status=?, identificador=?
                WHERE id_kitnet=?
            """
            self.__bd.executar(sql, (
                kitnet.numero, kitnet.quartos, kitnet.preco_padrao, 
                kitnet.status, kitnet.identificador, kitnet.id_kitnet
            ))
            return kitnet.id_kitnet
        else:
            sql = """
                INSERT INTO kitnet (numero, quartos, preco_padrao, status, identificador)
                VALUES (?, ?, ?, ?, ?)
            """
            id_gerado = self.__bd.executar(sql, (
                kitnet.numero, kitnet.quartos, kitnet.preco_padrao, 
                kitnet.status, kitnet.identificador
            ))
            kitnet.id_kitnet = id_gerado
            return id_gerado

    # Como o salvar já faz o update, esse método pode apenas redirecionar, gostei desse metodo
    def atualizar(self, kitnet: Kitnet):
        self.salvar(kitnet)

    # --- ADICIONADO PARA COMPLETAR O CRUD ---
    def deletar(self, id_kitnet: int) -> None:
        self.__bd.executar("DELETE FROM kitnet WHERE id_kitnet = ?", (id_kitnet,))

    def listar_todas(self) -> List[Kitnet]:
        sql = "SELECT id_kitnet, numero, quartos, preco_padrao, status, identificador FROM kitnet ORDER BY numero"
        rows = self.__bd.executar_query(sql)
        
        lista_kitnets = []
        for row in rows:
            ident = row[5] if row[5] else 'K'
            
            k = Kitnet(
                id_kitnet=row[0],
                numero=row[1],
                quartos=row[2],
                preco_padrao=row[3],
                status=row[4],
                identificador=ident
            )
            lista_kitnets.append(k)
        return lista_kitnets

    def buscar_por_id(self, id_kitnet: int) -> Optional[Kitnet]:
        sql = "SELECT id_kitnet, numero, quartos, preco_padrao, status, identificador FROM kitnet WHERE id_kitnet = ?"
        row = self.__bd.executar_query(sql, (id_kitnet,), fetchone=True)
        
        if row:
            ident = row[5] if row[5] else 'K'
            return Kitnet(
                id_kitnet=row[0], numero=row[1], quartos=row[2], 
                preco_padrao=row[3], status=row[4], identificador=ident
            )
        return None