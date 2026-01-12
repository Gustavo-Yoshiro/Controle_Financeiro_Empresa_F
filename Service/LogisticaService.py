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
            # data_fim fica None por padrão
        )
        id_contrato = self.dao_contrato.salvar(novo_c)
        
        # 3. Bloqueia Veículo (Muda status para alocado)
        v.status = 'alocado'
        self.dao_veiculo.salvar(v)

        # 4. Gera 1ª Cobrança (Mês Atual)
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
        
        # 1. Cálculos Financeiros
        # Soma o que já foi pago antes (se houver) com o que está entrando agora
        novo_total_pago = pag.valor_pago + valor_recebido
        
        # Calcula quanto ainda falta
        saldo_restante = pag.valor_esperado - novo_total_pago
        
        # Margem de tolerância de 5 centavos para considerar quitado
        if saldo_restante <= 0.05:
            pag.status = 'pago'
            # Ajusta visualmente para não ficar valor pago maior que esperado (opcional)
            # pag.valor_pago = pag.valor_esperado 
            pag.valor_pago = novo_total_pago 
        else:
            pag.status = 'parcial'
            pag.valor_pago = novo_total_pago

        # Atualiza a data do último pagamento
        pag.data_pagamento = date.today().strftime("%Y-%m-%d")
        
        # 2. Salva alterações no Banco
        self.dao_pagamento.salvar(pag) 

        # 3. Integração com Financeiro (Extrato)
        # Registra apenas o valor que entrou AGORA
        self.fin_service.registrar_receita_manual(
            descricao=f"Logística {pag.mes_referencia} ({obs})",
            valor=valor_recebido,
            id_categoria=5, # ID 5 = Receita Logística
            data=pag.data_pagamento, 
            banco=banco,
            forma="Boleto/Pix",
            id_pagamento_alocacao=pag.id_pagamento_alocacao # Vínculo importante
        )
        
        if pag.status == 'parcial':
            return f"Recebimento Parcial registrado. Resta pagar R$ {saldo_restante:.2f}."
        else:
            return "Fatura quitada com sucesso!"

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
            # Verifica se já existe boleto para este contrato neste mês
            existe = any(p.id_contrato_alocacao == c.id_contrato_alocacao and p.mes_referencia == mes_atual for p in pagamentos)
            if not existe:
                self._criar_boleto(c.id_contrato_alocacao, mes_atual, c.valor_mensal)
                count += 1
        return f"Processamento concluído. {count} novas faturas geradas."

    def listar_faturas_pendentes(self) -> List[Dict]:
        """
        Retorna lista de dicionários ricos para a interface.
        Usado para popular o SelectBox de pagamentos.
        """
        # Garante que boletos do mês existem antes de listar
        self.gerar_cobrancas_mensais()

        # Busca pendentes, atrasados e parciais
        pendentes = self.dao_pagamento.listar_pendentes()
        
        # Otimização: Carregar dados em memória
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
                
                # Calcula quanto falta pagar
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
            valor_pago=0.0,     # Começa zerado
            status='pendente', 
            data_pagamento=None
        )
        self.dao_pagamento.salvar(novo)