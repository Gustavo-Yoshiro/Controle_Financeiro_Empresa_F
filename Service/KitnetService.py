from typing import List, Dict
from Persistencia.Impl import KitnetImpl, ContratoKitnetImpl
from Persistencia.Entidades import Kitnet

class KitnetService:
    def __init__(self):
        self.dao = KitnetImpl()
        self.dao_contrato_validacao = ContratoKitnetImpl() 

    def cadastrar(self, numero: int, valor: float, identificador: str, quartos: int = 1, status: str = 'LIVRE') -> str:
        nova_kit = Kitnet(numero=numero, quartos=quartos, preco_padrao=valor, 
                          status=status, identificador=identificador)
        self.dao.salvar(nova_kit)
        return f"Sucesso: {identificador}-{numero} cadastrada!"

    def listar_livres_para_select(self) -> Dict[str, int]:
        """
        Retorna apenas kitnets LIVRES para preencher o combobox na hora de fazer contrato.
        Formato: {'K-101 (R$ 800.00)': id_kitnet}
        """
        todas = self.dao.listar_todas()
        livres = {}
        for k in todas:
            if k.status == 'LIVRE': # Regra de Negócio importante
                label = f"{k.identificador}-{k.numero} (R$ {k.preco_padrao:.2f})"
                livres[label] = k.id_kitnet
        return livres


    def admin_listar_todas(self) -> List[Kitnet]:
        return self.dao.listar_todas() 

    def admin_editar(self, id_k: int, num: int, ident: str, val: float, st: str, quartos: int) -> str:
        k = self.dao.buscar_por_id(id_k)
        if k:
            k.numero = num
            k.identificador = ident
            k.preco_padrao = val
            k.status = st
            k.quartos = quartos 
            
            self.dao.salvar(k) 
            return "Kitnet atualizada."
        return "Erro: Kitnet não encontrada."

    def admin_excluir(self, id_k: int) -> str:
        contratos = self.dao_contrato_validacao.listar_ativos()
        
        if any(c.id_kitnet == id_k for c in contratos):
            return "Erro: Não é possível excluir. Existe contrato ativo nesta kitnet."
        
        self.dao.deletar(id_k)
        return "Kitnet excluída."