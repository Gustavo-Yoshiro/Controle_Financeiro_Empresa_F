from typing import Dict, List
from Persistencia.Impl import EmpresaImpl
from Persistencia.Entidades import Empresa

class EmpresaService:
    def __init__(self):
        self.dao = EmpresaImpl()

    def cadastrar(self, razao: str, cnpj: str, tel: str) -> str:
        try:
            nova = Empresa(razao_social=razao, cnpj=cnpj, telefone=tel)
            self.dao.salvar(nova)
            return "Empresa cadastrada com sucesso!"
        except Exception as e:
            return f"Erro ao cadastrar: {e}"

    def listar_para_select(self) -> Dict[str, int]:
        """
        Retorna um dicionário {'Nome da Empresa': ID} 
        Ideal para preencher Selectbox no Streamlit.
        """
        lista = self.dao.listar_todas()
        return {e.razao_social: e.id_empresa for e in lista}


    def admin_listar_todas(self) -> List[Empresa]:
        return self.dao.listar_todas()

    def admin_editar(self, id_empresa: int, razao: str, cnpj: str, tel: str) -> str:
        emp = self.dao.buscar_por_id(id_empresa)
        if emp:
            emp.razao_social = razao
            emp.cnpj = cnpj
            emp.telefone = tel
            
            self.dao.salvar(emp) 
            return "Empresa atualizada."
        return "Erro: Empresa não encontrada."

    def admin_excluir(self, id_empresa: int) -> str:
        try:
            self.dao.deletar(id_empresa)
            return "Empresa excluída."
        except Exception as e:
            return f"Erro ao excluir: {e}"