from typing import List, Dict
from datetime import date

# Imports de Persistência
from Persistencia.Impl import ContratoAlocacaoImpl, PagamentoAlocacaoImpl, VeiculoImpl, EmpresaImpl

# Imports de Entidades
from Persistencia.Entidades import ContratoAlocacao, PagamentoAlocacao

# Integração
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
        
        # 1. Valida Veículo
        v = self.dao_veiculo.buscar_por_id(id_veiculo)
        if not v: return "Veículo não encontrado."
        if v.status != 'ativo': return f"Veículo indisponível (Status: {v.status})."

        # 2. Cria Contrato
        novo_c = ContratoAlocacao(
            id_empresa=id_empresa, 
            id_veiculo=id_veiculo, 
            valor_mensal=valor_mensal, 
            data_inicio=data_inicio,
            dia_vencimento=dia_venc, 
            ativo=1
        )
        id_contrato = self.dao_contrato.salvar(novo_c)
        
        # 3. Bloqueia Veículo (Muda status para alocado)
        v.status = 'alocado'
        self.dao_veiculo.salvar(v)

        # 4. Gera 1ª Cobrança (Mês Atual)
        mes_atual = str(data_inicio)[:7] 
        self._criar_boleto(id_contrato, mes_atual, valor_mensal)

        return "Contrato assinado e veículo alocado!"

    def processar_recebimento(self, id_pagamento: int, valor_recebido: float, banco: str) -> str:
        pag = self.dao_pagamento.buscar_por_id(id_pagamento)
        if not pag: return "Boleto não encontrado."
        if pag.status == 'pago': return "Erro: Já pago."
        
        # 1. Atualiza Boleto Local
        pag.valor_esperado = valor_recebido # Atualiza valor real
        pag.status = 'pago'
        pag.data_pagamento = date.today().strftime("%Y-%m-%d")
        self.dao_pagamento.salvar(pag) # Smart Save faz Update

        # 2. Envia dinheiro para o Financeiro
        self.fin_service.registrar_receita_manual(
            descricao=f"Fatura Logística - Ref: {pag.mes_referencia}",
            valor=valor_recebido,
            id_categoria=5, # ID 5 = Receita Logística
            data=pag.data_pagamento, 
            banco=banco,
            forma="Boleto/Pix"
        )
        return "Recebimento processado e lançado no caixa!"

    def encerrar_contrato(self, id_contrato: int, data_fim: str) -> str:
        c = self.dao_contrato.buscar_por_id(id_contrato)
        if not c: return "Contrato não encontrado."
        
        # 1. Finaliza contrato
        c.ativo = 0
        c.data_fim = data_fim
        self.dao_contrato.salvar(c)

        # 2. Libera Veículo
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

    def listar_faturas_pendentes(self) -> Dict[str, int]:
        """
        Gera dict formatado para o SelectBox:
        { 'Empresa X | Carro Y | R$ 500': id_pagamento }
        """
        # Garante que boletos do mês existem antes de listar
        self.gerar_cobrancas_mensais()

        pendentes = self.dao_pagamento.listar_pendentes()
        
        # Otimização: Carregar dados em memória
        contratos = {c.id_contrato_alocacao: c for c in self.dao_contrato.listar_ativos()}
        empresas = {e.id_empresa: e for e in self.dao_empresa.listar_todas()}
        veiculos = {v.id_veiculo: v for v in self.dao_veiculo.listar_todos()}

        opcoes = {}
        for p in pendentes:
            c = contratos.get(p.id_contrato_alocacao)
            if c:
                emp = empresas.get(c.id_empresa)
                car = veiculos.get(c.id_veiculo)
                
                nome_emp = emp.razao_social if emp else "?"
                nome_car = car.modelo if car else "?"
                
                texto = f"{nome_emp} | {nome_car} | Ref: {p.mes_referencia} | R$ {p.valor_esperado:.2f}"
                opcoes[texto] = p.id_pagamento_alocacao
        
        return opcoes

    def _criar_boleto(self, id_contrato, mes_ref, valor):
        novo = PagamentoAlocacao(
            id_contrato_alocacao=id_contrato, 
            mes_referencia=mes_ref,
            valor_esperado=valor, 
            status='pendente', 
            data_pagamento=None
        )
        self.dao_pagamento.salvar(novo)