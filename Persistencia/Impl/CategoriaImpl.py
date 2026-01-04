from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.Categoria import Categoria # Assumindo que criou este arquivo

class CategoriaImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, categoria: Categoria) -> int:
        sql = "INSERT INTO categoria (nome, tipo) VALUES (?, ?)"
        parametros = (categoria.nome, categoria.tipo)
        id_gerado = self.__bd.executar(sql, parametros)
        categoria.id_categoria = id_gerado
        return id_gerado

    def atualizar(self, categoria: Categoria) -> None:
        sql = "UPDATE categoria SET nome=?, tipo=? WHERE id_categoria=?"
        parametros = (categoria.nome, categoria.tipo, categoria.id_categoria)
        self.__bd.executar(sql, parametros)

    def deletar(self, id_categoria: int) -> None:
        sql = "DELETE FROM categoria WHERE id_categoria = ?"
        self.__bd.executar(sql, (id_categoria,))

    def listar_todas(self) -> List[Categoria]:
        sql = "SELECT id_categoria, nome, tipo FROM categoria"
        rows = self.__bd.executar_query(sql)
        return [Categoria(id_categoria=r[0], nome=r[1], tipo=r[2]) for r in rows]

