from typing import List, Optional
from Persistencia.Banco import BancoDeDados
# Importação limpa graças ao __init__.py que criamos
from Persistencia.Entidades import Categoria 

class CategoriaImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, categoria: Categoria) -> int:
        if categoria.id_categoria and categoria.id_categoria > 0:
            sql = "UPDATE categoria SET nome=?, tipo=? WHERE id_categoria=?"
            parametros = (categoria.nome, categoria.tipo, categoria.id_categoria)
            self.__bd.executar(sql, parametros)
            return categoria.id_categoria
        else:
            sql = "INSERT INTO categoria (nome, tipo) VALUES (?, ?)"
            parametros = (categoria.nome, categoria.tipo)
            id_gerado = self.__bd.executar(sql, parametros)
            
            categoria.id_categoria = id_gerado
            return id_gerado

    def deletar(self, id_categoria: int) -> None:
        sql = "DELETE FROM categoria WHERE id_categoria = ?"
        self.__bd.executar(sql, (id_categoria,))

    def listar_todas(self) -> List[Categoria]:
        sql = "SELECT id_categoria, nome, tipo FROM categoria"
        rows = self.__bd.executar_query(sql)
        return [
            Categoria(id_categoria=r[0], nome=r[1], tipo=r[2]) 
            for r in rows
        ]

    def buscar_por_id(self, id_categoria: int) -> Optional[Categoria]:
        """Essencial para a tela de Edição (ConfiguracoesPage)"""
        sql = "SELECT id_categoria, nome, tipo FROM categoria WHERE id_categoria = ?"
        row = self.__bd.executar_query_one(sql, (id_categoria,))
        
        if row:
            return Categoria(id_categoria=row[0], nome=row[1], tipo=row[2])
        return None
    def atualizar(self, categoria: Categoria) -> None:
        sql = "UPDATE categoria SET nome=?, tipo=? WHERE id_categoria=?"
        parametros = (categoria.nome, categoria.tipo, categoria.id_categoria)
        self.__bd.executar(sql, parametros)