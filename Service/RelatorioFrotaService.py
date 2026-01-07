from typing import List, Dict
from Persistencia.Impl import VeiculoImpl, EmpresaImpl, ContratoAlocacaoImpl, PagamentoAlocacaoImpl


class RelatorioFrotaService:
    def __init__(self):
        self.dao_veiculo = VeiculoImpl()
        self.dao_empresa = EmpresaImpl()
        self.dao_contrato = ContratoAlocacaoImpl()
        self.dao_pagamento = PagamentoAlocacaoImpl()

    def listar_frota_simples(self) -> List[Dict]:
        """Usado no filtro do Dashboard (Selectbox)"""
        veiculos = self.dao_veiculo.listar_todos()
        # Retorna apenas o necessário para preencher o combo
        return [{"id": v.id_veiculo, "modelo": v.modelo, "placa": v.placa} for v in veiculos]

    def listar_pendencias_formatadas(self) -> Dict[str, int]:
        """
        Gera o dict { 'Empresa X - Carro Y (R$ 500)': id_pagamento }
        Essencial para a tela de 'Receber Logística'.
        """
        pendentes = self.dao_pagamento.listar_pendentes()
        contratos = self.dao_contrato.listar_ativos()
        
        # Otimização de Performance: Carrega tudo em memória para evitar N+1
        # Cria dicionários {id: nome}
        empresas = {e.id_empresa: e.razao_social for e in self.dao_empresa.listar_todas()}
        veiculos = {v.id_veiculo: v.modelo for v in self.dao_veiculo.listar_todos()}
        
        opcoes = {}
        for p in pendentes:
            # Acha o contrato referente a este pagamento
            c = next((x for x in contratos if x.id_contrato_alocacao == p.id_contrato_alocacao), None)
            
            if c:
                nome_emp = empresas.get(c.id_empresa, "Empresa Desc.")
                nome_car = veiculos.get(c.id_veiculo, "Carro Desc.")
                
                # Texto bonito para o usuário selecionar
                texto = f"{nome_emp} | {nome_car} | Ref: {p.mes_referencia} | R$ {p.valor_esperado:.2f}"
                opcoes[texto] = p.id_pagamento_alocacao
                
        return opcoes

    # --- MÉTODOS PARA O DASHBOARD (GRÁFICOS E CARDS) ---

    def get_kpis_frota(self) -> Dict:
        """Retorna os totais para os Cards do topo"""
        veiculos = self.dao_veiculo.listar_todos()
        
        total = len(veiculos)
        alocados = len([v for v in veiculos if v.status == 'alocado'])
        disponiveis = len([v for v in veiculos if v.status == 'ativo'])
        manutencao = len([v for v in veiculos if v.status == 'manutencao'])
        
        # Taxa de Ocupação (Ex: 80%)
        taxa_ocupacao = (alocados / total * 100) if total > 0 else 0
        
        return {
            "total_veiculos": total,
            "alocados": alocados,
            "disponiveis": disponiveis,
            "manutencao": manutencao,
            "taxa_ocupacao": taxa_ocupacao
        }

    def get_faturamento_logistica(self) -> float:
        """Soma tudo que já foi pago em contratos de alocação"""
        pagamentos = self.dao_pagamento.listar_todos()
        return sum(p.valor_esperado for p in pagamentos if p.status == 'pago')