from typing import List, Dict, Optional
from datetime import date

# Imports de Persistência
from Persistencia.Impl import (
    VeiculoImpl, 
    EmpresaImpl, 
    ContratoAlocacaoImpl, 
    PagamentoAlocacaoImpl, 
    DividaVeiculoImpl
)
# Imports de Entidades
from Persistencia.Entidades import (
    Veiculo, 
    Empresa, 
    ContratoAlocacao, 
    PagamentoAlocacao, 
    DividaVeiculo
)
# IMPORTANTE: Importar o Financeiro para integrar o caixa
from Service.FinanceiroService import FinanceiroService

class TransporteService:
    def __init__(self):
        self.dao_veiculo = VeiculoImpl()
        self.dao_empresa = EmpresaImpl()
        self.dao_contrato = ContratoAlocacaoImpl()
        self.dao_fatura = PagamentoAlocacaoImpl()
        self.dao_divida = DividaVeiculoImpl()
        
        # Instância do Financeiro para comunicar gastos
        self.fin_service = FinanceiroService()

    # =========================================================================
    # GESTÃO DA FROTA E MANUTENÇÃO
    # =========================================================================

    def cadastrar_veiculo(self, modelo: str, placa: str, ano: int, finalidade: str) -> str:
        novo = Veiculo(
            modelo=modelo, 
            placa=placa.upper(), 
            ano=ano, 
            km_atual=0, 
            finalidade=finalidade, 
            status='ativo'
        )
        self.dao_veiculo.salvar(novo)
        return f"Veículo {modelo} ({placa}) cadastrado com sucesso."

    def registrar_divida_veiculo(self, id_veiculo: int, descricao: str, valor: float, vencimento: str) -> str:
        """
        Lança uma conta a pagar (IPVA, Manutenção agendada).
        Isso NÃO sai do caixa ainda, fica apenas como 'Pendente'.
        """
        nova_divida = DividaVeiculo(
            id_veiculo=id_veiculo,
            descricao=descricao,
            valor=valor,
            data_vencimento=vencimento,
            status='pendente'
        )
        self.dao_divida.salvar(nova_divida)
        return "Dívida/Manutenção agendada registrada."

    def pagar_divida_veiculo(self, id_divida: int, banco: str, forma: str, data_pagamento: str = None) -> str:
        """
        Baixa a dívida e tira o dinheiro do caixa (Agora pede Banco e Forma).
        """
        # 1. Busca a dívida
        divida = self.dao_divida.buscar_por_id(id_divida)
        if not divida:
            return "Erro: Dívida não encontrada."
        if divida.status == 'pago':
            return "Erro: Dívida já paga."

        # 2. Atualiza status da dívida localmente
        divida.status = 'pago'
        self.dao_divida.atualizar(divida)

        # 3. Lança no Financeiro (Com Banco e Forma)
        # Usamos o método do FinanceiroService para garantir integridade
        data_final = data_pagamento if data_pagamento else date.today().strftime("%Y-%m-%d")
        
        self.fin_service.registrar_despesa_veiculo(
            descricao=f"Pgto Dívida: {divida.descricao}",
            valor=divida.valor,
            id_veiculo=divida.id_veiculo,
            data_gasto=data_final,
            banco=banco,       # <--- Novo
            forma=forma        # <--- Novo
        )
        
        return "Sucesso: Dívida paga e descontada do saldo."

    def lancar_gasto_direto(self, id_veiculo: int, descricao: str, valor: float, 
                            data: str, banco: str, forma: str) -> str:
        """
        Para gastos rápidos (Gasolina, Lavagem) que não precisam virar dívida antes.
        Vai direto para o financeiro.
        """
        veiculo = self.dao_veiculo.buscar_por_id(id_veiculo)
        desc_final = f"{veiculo.modelo}: {descricao}"
        
        msg = self.fin_service.registrar_despesa_veiculo(
            descricao=desc_final,
            valor=valor,
            id_veiculo=id_veiculo,
            data_gasto=data,
            banco=banco,
            forma=forma
        )
        return msg

    # =========================================================================
    # GESTÃO DE ALOCAÇÃO (Receitas de Contratos)
    # =========================================================================

    def criar_contrato_empresa(self, id_empresa: int, id_veiculo: int, valor: float, dia_venc: int) -> str:
        veiculo = self.dao_veiculo.buscar_por_id(id_veiculo)
        if not veiculo:
            return "Erro: Veículo não encontrado."

        contrato = ContratoAlocacao(
            id_empresa=id_empresa,
            id_veiculo=id_veiculo,
            valor_mensal=valor,
            dia_vencimento=dia_venc,
            ativo=1
        )
        self.dao_contrato.salvar(contrato)
        return "Contrato criado."

    def gerar_fatura_mensal(self, id_contrato: int, mes_ref: str, valor: float = None) -> str:
        """ Gera a cobrança (A Receber) """
        valor_final = valor
        if not valor_final:
            c = self.dao_contrato.buscar_por_id(id_contrato) # Supondo que exista esse método
            if c: valor_final = c.valor_mensal
            else: return "Erro: Contrato não achado."

        fatura = PagamentoAlocacao(
            id_contrato_alocacao=id_contrato,
            mes_referencia=mes_ref,
            valor_esperado=valor_final,
            status='pendente'
        )
        self.dao_fatura.salvar(fatura)
        return f"Fatura {mes_ref} gerada."

    def receber_fatura_empresa(self, id_fatura: int, banco: str, forma: str, data_pagamento: str = None) -> str:
        """
        Recebe o dinheiro da empresa e lança no caixa.
        """
        fatura = self.dao_fatura.buscar_por_id(id_fatura)
        if not fatura: return "Erro: Fatura não encontrada."
        if fatura.status == 'pago': return "Erro: Já paga."

        # 1. Baixa Fatura
        fatura.status = 'pago'
        fatura.data_pagamento = data_pagamento if data_pagamento else date.today().strftime("%Y-%m-%d")
        self.dao_fatura.atualizar(fatura)

        # 2. Lança Receita no Financeiro (Usando Receita Manual por enquanto)
        # O ideal seria ter um método 'registrar_receita_veiculo' no financeiro, 
        # mas vamos usar o manual passando a descrição clara.
        self.fin_service.registrar_receita_manual(
            descricao=f"Recebimento Alocação - Ref: {fatura.mes_referencia}",
            valor=fatura.valor_esperado,
            id_categoria=3, # Categoria Transporte
            data_receita=fatura.data_pagamento,
            banco=banco,     # <--- Novo
            forma=forma      # <--- Novo
        )

        return "Pagamento recebido e lançado no caixa."

    def listar_frota_simples(self) -> List[Dict]:
        """ Helper para a UI """
        veiculos = self.dao_veiculo.listar_todos()
        lista = []
        for v in veiculos:
            lista.append({
                "id": v.id_veiculo,
                "modelo": v.modelo,
                "placa": v.placa,
                "status": v.status,
                "finalidade": v.finalidade
            })
        return lista