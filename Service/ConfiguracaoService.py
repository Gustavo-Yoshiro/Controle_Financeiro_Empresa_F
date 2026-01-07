from typing import List, Dict
from Persistencia.Impl import ConfiguracaoImpl

class ConfiguracaoService:
    def __init__(self):
        self.dao = ConfiguracaoImpl()

    # =========================================================================
    # BANCOS
    # =========================================================================
    def listar_bancos(self) -> List[str]:
        return self.dao.listar_bancos()

    def adicionar_banco(self, nome: str) -> str:
        try:
            if not nome: return "Nome vazio."
            self.dao.adicionar_banco(nome)
            return "Banco adicionado!"
        except Exception as e:
            return f"Erro ao adicionar (Verifique se já existe): {e}"

    def editar_banco(self, nome_antigo: str, novo_nome: str) -> str:
        try:
            self.dao.atualizar_banco(nome_antigo, novo_nome)
            return f"Banco renomeado para {novo_nome}."
        except Exception as e:
            return f"Erro ao editar: {e}"

    def excluir_banco(self, nome: str) -> str:
        try:
            # Regra de Negócio: Não apagar se estiver em uso
            if self.dao.banco_esta_em_uso(nome):
                return "Não é possível excluir: Existem transações usando este banco."
            
            self.dao.deletar_banco(nome)
            return "Banco removido com sucesso."
        except Exception as e:
            return f"Erro ao excluir: {e}"

    # =========================================================================
    # FORMAS DE PAGAMENTO
    # =========================================================================
    def listar_formas(self) -> List[str]:
        return self.dao.listar_formas()

    def adicionar_forma(self, nome: str) -> str:
        try:
            self.dao.adicionar_forma(nome)
            return "Forma adicionada!"
        except Exception as e:
            return f"Erro: {e}"

    def editar_forma(self, nome_antigo: str, novo_nome: str) -> str:
        try:
            self.dao.atualizar_forma(nome_antigo, novo_nome)
            return f"Forma renomeada para {novo_nome}."
        except Exception as e:
            return f"Erro: {e}"

    def excluir_forma(self, nome: str) -> str:
        try:
            if self.dao.forma_esta_em_uso(nome):
                return "Em uso em transações. Não pode excluir."
            
            self.dao.deletar_forma(nome)
            return "Forma removida."
        except Exception as e:
            return f"Erro: {e}"

    # =========================================================================
    # CATEGORIAS
    # =========================================================================
    def listar_categorias(self) -> List[Dict]:
        return self.dao.listar_categorias()

    def adicionar_categoria(self, nome: str, tipo: str) -> str:
        try:
            self.dao.adicionar_categoria(nome, tipo)
            return "Categoria adicionada!"
        except Exception as e:
            return f"Erro: {e}"

    def editar_categoria(self, id_cat: int, novo_nome: str) -> str:
        try:
            self.dao.atualizar_categoria(id_cat, novo_nome)
            return "Categoria atualizada."
        except Exception as e:
            return f"Erro: {e}"

    def excluir_categoria(self, id_cat: int) -> str:
        try:
            if self.dao.categoria_esta_em_uso(id_cat):
                return "Categoria usada em lançamentos. Não pode excluir."
            
            self.dao.deletar_categoria(id_cat)
            return "Categoria removida."
        except Exception as e:
            return f"Erro: {e}"
        
    