from typing import List, Dict
from datetime import date
from Persistencia.Impl import VeiculoImpl, EmpresaImpl, ContratoAlocacaoImpl, PagamentoAlocacaoImpl

class RelatorioFrotaService:
    def __init__(self):
        self.dao_veiculo = VeiculoImpl()
        self.dao_empresa = EmpresaImpl()
        self.dao_contrato = ContratoAlocacaoImpl()
        self.dao_pagamento = PagamentoAlocacaoImpl()

    def gerar_painel_frota(self, mes_ref: str = None) -> List[dict]:
        """
        Gera a tabela inteligente para o Dashboard.
        Analisa mês a mês se pagou, se deve, e calcula dívida antiga.
        """
        if not mes_ref:
            mes_ref = date.today().strftime("%Y-%m")

        # Carrega dados
        todos_veiculos = self.dao_veiculo.listar_todos()
        todos_contratos = self.dao_contrato.listar_ativos()
        todos_pagamentos = self.dao_pagamento.listar_todos()
        todas_empresas = self.dao_empresa.listar_todas()

        tabela = []

        for v in todos_veiculos:
            # 1. Estrutura Base
            linha = {
                "ID": v.id_veiculo,
                "Veículo": f"{v.modelo} ({v.placa})",
                "Status": v.status.upper(),
                "Empresa": "---",
                "Situação Mês": "LIVRE", # Padrão se não tiver contrato
                "Valor": "---",
                "Alertas": ""
            }

            # 2. Busca Contrato Ativo
            contrato = next((c for c in todos_contratos if c.id_veiculo == v.id_veiculo and c.ativo == 1), None)

            if contrato:
                empresa = next((e for e in todas_empresas if e.id_empresa == contrato.id_empresa), None)
                linha["Empresa"] = empresa.razao_social if empresa else "?"
                linha["Valor"] = f"R$ {contrato.valor_mensal:.2f}"
                
                # Pega todos os pagamentos deste contrato
                pags_contrato = [p for p in todos_pagamentos if p.id_contrato_alocacao == contrato.id_contrato_alocacao]

                # --- LÓGICA A: Dívida Acumulada (Passado) ---
                divida_acumulada = 0.0
                qtd_atrasados = 0
                
                for p in pags_contrato:
                    # Se o mês do pagamento for ANTERIOR ao mês que estamos olhando
                    if p.mes_referencia < mes_ref:
                        # Se não estiver totalmente pago
                        if p.status != 'pago':
                            falta = p.valor_esperado - p.valor_pago
                            if falta > 0.05: # Ignora centavos
                                divida_acumulada += falta
                                qtd_atrasados += 1
                
                if qtd_atrasados > 0:
                    linha["Alertas"] = f"⚠️ {qtd_atrasados} pend. (R$ {divida_acumulada:.2f})"

                # --- LÓGICA B: Situação do Mês Selecionado (Presente) ---
                pag_mes = next((p for p in pags_contrato if p.mes_referencia == mes_ref), None)

                if not pag_mes:
                    linha["Situação Mês"] = "⚪ Aguardando Geração"
                else:
                    if pag_mes.status == 'pago':
                        linha["Situação Mês"] = "✅ PAGO"
                    
                    elif pag_mes.status == 'parcial':
                        falta = pag_mes.valor_esperado - pag_mes.valor_pago
                        linha["Situação Mês"] = f"🟡 PARCIAL (Falta R$ {falta:.2f})"
                    
                    else: # pendente ou atrasado
                        hoje_str = date.today().strftime("%Y-%m-%d")
                        try:
                            # Monta data de vencimento YYYY-MM-DD
                            venc_str = f"{mes_ref}-{contrato.dia_vencimento:02d}"
                        except:
                            venc_str = f"{mes_ref}-10"

                        if hoje_str > venc_str:
                            linha["Situação Mês"] = f"🔴 ATRASADO ({contrato.dia_vencimento})"
                        else:
                            linha["Situação Mês"] = f"⏳ A VENCER ({contrato.dia_vencimento})"

            tabela.append(linha)
        
        # Ordena: Quem tem Alerta primeiro, depois por nome
        return sorted(tabela, key=lambda x: (x['Alertas'] == "", x['Veículo']))

    def listar_frota_simples(self) -> List[Dict]:
        """Usado no filtro do Dashboard (Selectbox)"""
        veiculos = self.dao_veiculo.listar_todos()
        return [{"id": v.id_veiculo, "modelo": v.modelo, "placa": v.placa} for v in veiculos]

    def listar_pendencias_formatadas(self) -> Dict[str, int]:
        """
        Gera o dict para o SelectBox de Recebimento.
        Agora mostra quanto FALTA pagar (para casos parciais).
        """
        pendentes = self.dao_pagamento.listar_pendentes() # Traz pendentes, atrasados e parciais
        contratos = self.dao_contrato.listar_ativos()
        
        empresas = {e.id_empresa: e.razao_social for e in self.dao_empresa.listar_todas()}
        veiculos = {v.id_veiculo: v.modelo for v in self.dao_veiculo.listar_todos()}
        
        opcoes = {}
        for p in pendentes:
            c = next((x for x in contratos if x.id_contrato_alocacao == p.id_contrato_alocacao), None)
            
            if c:
                nome_emp = empresas.get(c.id_empresa, "Empresa Desc.")
                nome_car = veiculos.get(c.id_veiculo, "Carro Desc.")
                
                # CÁLCULO DO RESTANTE
                restante = p.valor_esperado - p.valor_pago
                
                texto = f"{nome_emp} | {nome_car} | Ref: {p.mes_referencia} | Falta: R$ {restante:.2f}"
                opcoes[texto] = p.id_pagamento_alocacao
                
        return opcoes

    # --- KPI's ---

    def get_kpis_frota(self) -> Dict:
        veiculos = self.dao_veiculo.listar_todos()
        total = len(veiculos)
        alocados = len([v for v in veiculos if v.status == 'alocado'])
        disponiveis = len([v for v in veiculos if v.status == 'ativo'])
        manutencao = len([v for v in veiculos if v.status == 'manutencao'])
        taxa = (alocados / total * 100) if total > 0 else 0
        
        return {
            "total_veiculos": total,
            "alocados": alocados,
            "disponiveis": disponiveis,
            "manutencao": manutencao,
            "taxa_ocupacao": taxa
        }

    def get_faturamento_logistica(self) -> float:
        """Soma o valor_pago real de todos os registros"""
        pagamentos = self.dao_pagamento.listar_todos()
        # Soma o que realmente entrou no caixa (valor_pago), não a expectativa
        return sum(p.valor_pago for p in pagamentos)