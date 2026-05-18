from typing import List, Dict
from Persistencia.Impl import CategoriaImpl
from Persistencia.Entidades import Categoria

class CategoriaService:
    def __init__(self):
        self.dao = CategoriaImpl()

    def listar_todas(self) -> List[Dict]:
        """ Retorna dicts para facilitar o uso em Selectbox/Combobox na UI """
        cats = self.dao.listar_todas()
        return [{"id": c.id_categoria, "nome": c.nome, "tipo": c.tipo} for c in cats]
    
    def buscar_nome_por_id(self, id_cat: int) -> str:
        """ 
        OTIMIZAÇÃO: Usa o método específico do DAO em vez de listar tudo.
        Isso poupa memória e processamento.
        """
        cat = self.dao.buscar_por_id(id_cat)
        if cat:
            return cat.nome
        return "Desconhecido"


    def salvar_categoria(self, nome: str, tipo: str, id_categoria: int = None) -> str:
        nova = Categoria(id_categoria=id_categoria, nome=nome, tipo=tipo)
        self.dao.salvar(nova) 
        return "Categoria salva com sucesso."

    def excluir_categoria(self, id_categoria: int) -> str:
        self.dao.deletar(id_categoria)
        return "Categoria excluída."