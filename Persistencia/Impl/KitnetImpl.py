from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.Kitnet import Kitnet

class KitnetImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, kitnet: Kitnet) -> int:
        """
        Insere uma nova kitnet no banco e retorna o ID gerado.
        """
        sql = """
            INSERT INTO kitnet (numero, quartos, preco_padrao, status)
            VALUES (?, ?, ?, ?)
        """
        parametros = (
            kitnet.numero,
            kitnet.quartos,
            kitnet.preco_padrao,
            kitnet.status
        )
        # Executa o insert e recupera o ID gerado pelo banco
        id_gerado = self.__bd.executar(sql, parametros)
        
        # Atualiza o objeto com o ID gerado
        kitnet.id_kitnet = id_gerado
        
        return id_gerado

    def atualizar(self, kitnet: Kitnet) -> None:
        """
        Atualiza os dados de uma kitnet existente.
        """
        sql = """
            UPDATE kitnet 
            SET numero = ?, quartos = ?, preco_padrao = ?, status = ?
            WHERE id_kitnet = ?
        """
        parametros = (
            kitnet.numero,
            kitnet.quartos,
            kitnet.preco_padrao,
            kitnet.status,
            kitnet.id_kitnet
        )
        self.__bd.executar(sql, parametros)

    def deletar(self, id_kitnet: int) -> None:
        """
        Remove uma kitnet pelo ID.
        """
        sql = "DELETE FROM kitnet WHERE id_kitnet = ?"
        self.__bd.executar(sql, (id_kitnet,))

    def buscar_por_id(self, id_kitnet: int) -> Optional[Kitnet]:
        """
        Busca uma kitnet específica. Retorna o objeto ou None se não achar.
        """
        sql = "SELECT id_kitnet, numero, quartos, preco_padrao, status FROM kitnet WHERE id_kitnet = ?"
        row = self.__bd.executar_query(sql, (id_kitnet,), fetchone=True)
        
        if row:
            return Kitnet(
                id_kitnet=row[0],
                numero=row[1],
                quartos=row[2],
                preco_padrao=row[3],
                status=row[4]
            )
        return None

    def listar_todas(self) -> List[Kitnet]:
        """
        Retorna uma lista com todas as kitnets cadastradas.
        """
        sql = "SELECT id_kitnet, numero, quartos, preco_padrao, status FROM kitnet"
        rows = self.__bd.executar_query(sql)
        
        # Converte cada linha do banco (tupla) em um objeto Kitnet
        lista_kitnets = []
        for row in rows:
            k = Kitnet(
                id_kitnet=row[0],
                numero=row[1],
                quartos=row[2],
                preco_padrao=row[3],
                status=row[4]
            )
            lista_kitnets.append(k)
            
        return lista_kitnets