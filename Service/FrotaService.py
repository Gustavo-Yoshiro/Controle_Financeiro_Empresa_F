from typing import List, Dict
from Persistencia.Impl import VeiculoImpl
from Persistencia.Entidades import Veiculo
from Service import FinanceiroService

class FrotaService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao_veiculo = VeiculoImpl()
        # Injeção opcional
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    def cadastrar(self, modelo: str, placa: str, ano: int, finalidade: str) -> str:
        novo = Veiculo(
            modelo=modelo, 
            placa=placa.upper(), 
            ano=ano, 
            finalidade=finalidade, 
            status='ativo'
        )
        self.dao_veiculo.salvar(novo)
        return f"Veículo {modelo} ({placa}) cadastrado com sucesso."

    def lancar_manutencao(self, id_veiculo: int, descricao: str, valor: float, 
                          data: str, banco: str, forma: str) -> str:
        """
        Lança despesa de manutenção e envia direto para o Financeiro.
        """
        veiculo = self.dao_veiculo.buscar_por_id(id_veiculo)
        if not veiculo: return "Erro: Veículo não encontrado."

        nome_carro = f"{veiculo.modelo} ({veiculo.placa})"
        desc_final = f"[{nome_carro}] {descricao}"
        
        # Chama o Facade Financeiro (Garante ID Categoria correto lá dentro)
        return self.fin_service.registrar_despesa_veiculo(
            descricao=desc_final, 
            valor=valor, 
            id_veiculo=id_veiculo,
            data=data, 
            banco=banco, 
            forma=forma
        )
    
    def listar_frota_simples(self) -> List[Dict]:
        """Retorna dicts leves para preencher Selectbox"""
        veiculos = self.dao_veiculo.listar_todos()
        return [{
            "id": v.id_veiculo, 
            "label": f"{v.modelo} - {v.placa} ({v.status})"
        } for v in veiculos]

    # --- ADMINISTRAÇÃO (CRUD) ---
    
    def admin_listar_todos(self) -> List[Veiculo]:
        return self.dao_veiculo.listar_todos()
    
    def admin_editar(self, id_v: int, modelo: str, placa: str, ano: int, finalidade: str, status: str) -> str:
        v = self.dao_veiculo.buscar_por_id(id_v)
        if v:
            v.modelo = modelo
            v.placa = placa.upper()
            v.ano = ano
            v.finalidade = finalidade
            v.status = status
            self.dao_veiculo.salvar(v) # Smart Save
            return "Veículo atualizado."
        return "Erro: Veículo não encontrado."

    def admin_excluir(self, id_veiculo: int) -> str:
        self.dao_veiculo.deletar(id_veiculo)
        return "Veículo excluído da frota."