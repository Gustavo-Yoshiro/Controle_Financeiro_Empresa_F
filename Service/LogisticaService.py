from typing import List, Dict
from datetime import date

from Persistencia.Impl import ContratoAlocacaoImpl, PagamentoAlocacaoImpl, VeiculoImpl, EmpresaImpl

from Persistencia.Entidades import ContratoAlocacao, PagamentoAlocacao

from Service import FinanceiroService

class LogisticaService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao_contrato = ContratoAlocacaoImpl()
        self.dao_pagamento = PagamentoAlocacaoImpl()
        self.dao_veiculo = VeiculoImpl()
        self.dao_empresa = EmpresaImpl()
        
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    def criar_contrato(self, id_empresa: int, id_veiculo: int, valor_mensal: float, 
                       dia_venc: int, data_inicio: str) -> str:
        
        v = self.dao_veiculo.buscar_por_id(id_veiculo)
        if not v: return "Veículo não encontrado."
        if v.status != 'ativo': return f"Veículo indisponível (Status: {v.status})."

        novo_c = ContratoAlocacao(
            id_empresa=id_empresa, 
            id_veiculo=id_veiculo, 
            valor_mensal=valor_mensal, 
            data_inicio=data_inicio,
            dia_vencimento=dia_venc, 
            ativo=1
        )
        id_contrato = self.dao_contrato.salvar(novo_c)
        
        v.status = 'alocado'
        self.dao_veiculo.salvar(v)

        mes_atual = str(data_inicio)[:7] 
        self._criar_boleto(id_contrato, mes_atual, valor_mensal)

        return "Contrato assinado e veículo alocado!"

    def processar_recebimento(self, id_pagamento: int, valor_recebido: float, banco: str, obs: str = "") -> str:
        """
        Lógica Inteligente de Pagamento (Total ou Parcial)
        """
        pag = self.dao_pagamento.buscar_por_id(id_pagamento)
        if not pag: return "Boleto não encontrado."
        if pag.status == 'pago': return "Erro: Esta fatura já consta como paga."
        
        novo_total_pago = pag.valor_pago + valor_recebido
        
        saldo_restante = pag.valor_esperado - novo_total_pago
        
        if saldo_restante <= 0.05:
            pag.status = 'pago' 
            pag.valor_pago = novo_total_pago 
        else:
            pag.status = 'parcial'
            pag.valor_pago = novo_total_pago

        pag.data_pagamento = date.today().strftime("%Y-%m-%d")
        
        self.dao_pagamento.salvar(pag) 

        self.fin_service.registrar_receita_manual(
            descricao=f"Logística {pag.mes_referencia} ({obs})",
            valor=valor_recebido,
            id_categoria=5, 
            data=pag.data_pagamento, 
            banco=banco,
            forma="Boleto/Pix",
            id_pagamento_alocacao=pag.id_pagamento_alocacao 
        )
        
        if pag.status == 'parcial':
            return f"Recebimento Parcial registrado. Resta pagar R$ {saldo_restante:.2f}."
        else:
            return "Fatura quitada com sucesso!"

    def encerrar_contrato(self, id_contrato: int, data_fim: str) -> str:
        c = self.dao_contrato.buscar_por_id(id_contrato)
        if not c: return "Contrato não encontrado."
        
        c.ativo = 0
        c.data_fim = data_fim
        self.dao_contrato.salvar(c)

        v = self.dao_veiculo.buscar_por_id(c.id_veiculo)
        if v:
            v.status = 'ativo'
            self.dao_veiculo.salvar(v)
            
        return "Contrato encerrado. Veículo liberado."

    def gerar_cobrancas_mensais(self) -> str:
        """Verifica se virou o mês e gera novos boletos"""
        contratos = self.dao_contrato.listar_ativos()
        pagamentos = self.dao_pagamento.listar_todos()
        mes_atual = date.today().strftime("%Y-%m")
        count = 0

        for c in contratos:
            existe = any(p.id_contrato_alocacao == c.id_contrato_alocacao and p.mes_referencia == mes_atual for p in pagamentos)
            if not existe:
                self._criar_boleto(c.id_contrato_alocacao, mes_atual, c.valor_mensal)
                count += 1
        return f"Processamento concluído. {count} novas faturas geradas."

    def listar_faturas_pendentes(self) -> List[Dict]:
        self.gerar_cobrancas_mensais()

        pendentes = self.dao_pagamento.listar_pendentes()
        
        contratos = {c.id_contrato_alocacao: c for c in self.dao_contrato.listar_ativos()}
        empresas = {e.id_empresa: e for e in self.dao_empresa.listar_todas()}
        veiculos = {v.id_veiculo: v for v in self.dao_veiculo.listar_todos()}

        lista_formatada = []
        for p in pendentes:
            c = contratos.get(p.id_contrato_alocacao)
            if c:
                emp = empresas.get(c.id_empresa)
                car = veiculos.get(c.id_veiculo)
                
                nome_emp = emp.razao_social if emp else "?"
                nome_car = car.modelo if car else "?"
                
                restante = p.valor_esperado - p.valor_pago
                
                label = f"{nome_emp} | {nome_car} | Ref: {p.mes_referencia} | Falta: R$ {restante:.2f}"
                
                lista_formatada.append({
                    "label_combo": label,
                    "id_pagamento": p.id_pagamento_alocacao,
                    "valor_total_esperado": p.valor_esperado,
                    "valor_ja_pago": p.valor_pago,
                    "valor_restante": restante
                })
        
        return lista_formatada

    def _criar_boleto(self, id_contrato, mes_ref, valor):
        novo = PagamentoAlocacao(
            id_contrato_alocacao=id_contrato, 
            mes_referencia=mes_ref,
            valor_esperado=valor, 
            valor_pago=0.0,     
            status='pendente', 
            data_pagamento=None
        )
        self.dao_pagamento.salvar(novo)