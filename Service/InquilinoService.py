from typing import List, Dict
from Persistencia.Impl import InquilinoImpl
from Persistencia.Entidades import Inquilino

class InquilinoService:
    def __init__(self):
        self.dao = InquilinoImpl()

    def cadastrar(self, nome, cpf, telefone, sexo, est_civil, prof, email, obs) -> str:
        novo = Inquilino(nome=nome, cpf=cpf, telefone=telefone, sexo=sexo, 
                         estado_civil=est_civil, profissao=prof, email=email, obs=obs)
        self.dao.salvar(novo)
        return f"Inquilino {nome} cadastrado com sucesso!"

    def listar_simples(self) -> Dict[str, int]:
        """
        Retorna {'Nome do Inquilino': ID}
        Útil para preencher comboboxes/selects na hora de fazer contrato
        """
        lista = self.dao.listar_todos()
        return {i.nome: i.id_inquilino for i in lista}

    
    def admin_listar_todos(self) -> List[Inquilino]:
        return self.dao.listar_todos()

    def admin_editar(self, id_i: int, nome: str, cpf: str, telefone: str, 
                     sexo: str, est_civil: str, prof: str, email: str, obs: str) -> str:
        i = self.dao.buscar_por_id(id_i)
        if i:
            i.nome = nome
            i.cpf = cpf
            i.telefone = telefone
            i.sexo = sexo
            i.estado_civil = est_civil
            i.profissao = prof
            i.email = email
            i.obs = obs
            
            self.dao.salvar(i) 
            return "Dados do inquilino atualizados."
        return "Erro: Inquilino não encontrado."

    def admin_excluir(self, id_i: int) -> str:
        self.dao.deletar(id_i)
        return "Inquilino excluído."