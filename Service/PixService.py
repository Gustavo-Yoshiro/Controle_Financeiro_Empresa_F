from typing import List, Optional
from Persistencia.Impl.PixImpl import PixImpl
from Persistencia.Entidades.Pix import Pix

class PixService:
    def __init__(self):
        self.dao = PixImpl()

    def cadastrar_pix(self, titulo, chave, tipo, titular, banco) -> str:
        # 1. VERIFICA DUPLICIDADE
        # Remove espaços em branco das pontas para garantir
        chave_limpa = chave.strip()
        
        if self.dao.buscar_por_chave(chave_limpa):
            return f"Erro: A chave '{chave_limpa}' já está cadastrada!"

        # 2. SE NÃO EXISTE, SALVA
        novo_pix = Pix(
            titulo=titulo,
            chave=chave_limpa,
            tipo=tipo,
            titular=titular,
            banco=banco,
            favorito=0
        )
        self.dao.salvar(novo_pix)
        return "Sucesso: Nova chave Pix cadastrada!"


    def editar_pix(self, id_pix: int, titulo: str, chave: str, tipo: str, titular: str, banco: str) -> str:
        # 1. Busca o objeto original usando o DAO
        pix = self.dao.buscar_por_id(id_pix)
        if not pix: return "Erro: Pix não encontrado."

        # 2. Atualiza os dados
        pix.titulo = titulo
        pix.chave = chave
        pix.tipo = tipo
        pix.titular = titular
        pix.banco = banco
        
        # 3. Manda o DAO salvar (Smart Save faz Update)
        self.dao.salvar(pix)
        return "Pix atualizado com sucesso!"

    def alternar_favorito(self, id_pix: int, status_atual: int):
        # Se é 0 vira 1, se é 1 vira 0
        novo_status = 1 if status_atual == 0 else 0
        self.dao.atualizar_favorito(id_pix, novo_status)

    def excluir_pix(self, id_pix: int):
        # CORREÇÃO: Padronizado para 'deletar' conforme o DAO
        self.dao.deletar(id_pix)

    def listar_pix(self, termo_busca: str = "") -> List[Pix]:
        """ Lista todos, filtra pelo termo e ordena (Favoritos primeiro) """
        todos = self.dao.listar_todos()
        
        if termo_busca:
            termo = termo_busca.lower()
            # Filtra por Titulo ou Nome do Titular
            todos = [p for p in todos if termo in p.titulo.lower() or termo in p.titular.lower()]
        
        # Ordenação mágica: Primeiro pelo favorito (decrescente), depois alfabético
        todos.sort(key=lambda x: (-x.favorito, x.titulo.lower()))
        return todos

    def buscar_por_id(self, id_pix: int) -> Optional[Pix]:
        return self.dao.buscar_por_id(id_pix)
    
    def alternar_favorito(self, id_pix: int, novo_status: int):
        # O Service apenas confia no status que a Page mandou e repassa pro DAO
        self.dao.atualizar_favorito(id_pix, novo_status)