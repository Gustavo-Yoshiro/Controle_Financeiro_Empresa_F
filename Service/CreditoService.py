from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List, Dict

from Persistencia.Impl import BoletoImpl ,CartaoCreditoImpl
from Persistencia.Entidades import CartaoCredito, Boleto
from Service.FinanceiroService import FinanceiroService

class CreditoService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao_cartao = CartaoCreditoImpl()
        self.dao_boleto = BoletoImpl() # Acessa a tabela onde as compras estão salvas
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    # --- 1. CONFIGURAÇÃO ---
    def cadastrar_config_cartao(self, nome: str, dia_fech: int, dia_venc: int, limite: float, bandeira: str = "") -> str:
        if not nome: return "Erro: Nome do cartão é obrigatório."
        novo_cartao = CartaoCredito(nome=nome, dia_fechamento=dia_fech, dia_vencimento=dia_venc, limite=limite, bandeira=bandeira)
        res = self.dao_cartao.salvar(novo_cartao)
        return f"Cartão '{nome}' configurado com sucesso!" if res else "Erro ao cadastrar cartão."

    def listar_nomes_cartoes(self) -> List[str]:
        cartoes = self.dao_cartao.listar_todos()
        return [c.nome for c in cartoes] if cartoes else []

    # --- NOVO: CÁLCULO DE LIMITE ---
    def get_info_limite(self, nome_cartao: str) -> Dict:
        """
        Calcula o limite total, usado e disponível baseando-se nas parcelas pendentes.
        """
        cartao = self.dao_cartao.buscar_por_nome(nome_cartao)
        if not cartao: 
            return {"total": 0.0, "usado": 0.0, "disponivel": 0.0}
        
        limite_total = cartao.limite
        
        # Busca todas as dívidas pendentes deste cartão
        todos_boletos = self.dao_boleto.listar_todos()
        
        # O Pulo do Gato: Soma TUDO que é 'pendente' ligado a esse cartão.
        # Isso inclui a fatura do mês atual E as parcelas de 2026, 2027...
        usado = sum(b.valor for b in todos_boletos if b.banco_cartao == nome_cartao and b.status == 'pendente')
        
        return {
            "total": limite_total,
            "usado": usado,
            "disponivel": limite_total - usado
        }

    # --- 2. LANÇAMENTO INTELIGENTE (COM TRAVA DE LIMITE) ---
    def registrar_compra_inteligente(self, descricao: str, valor_total: float, data_compra_str: str, 
                                     id_categoria: int, nome_cartao: str, parcelas: int = 1) -> str:
        try:
            # 1. Validação de Limite
            info_limite = self.get_info_limite(nome_cartao)
            if info_limite['total'] > 0: # Só valida se tiver limite configurado (> 0)
                if valor_total > info_limite['disponivel']:
                    return f"Erro: Limite Insuficiente! Compra: R$ {valor_total:.2f} | Disponível: R$ {info_limite['disponivel']:.2f}"

            # 2. Busca configurações do cartão (dias)
            cartao = self.dao_cartao.buscar_por_nome(nome_cartao)
            dia_fech = cartao.dia_fechamento if cartao else 1
            dia_venc = cartao.dia_vencimento if cartao else 10
            
            data_compra = datetime.strptime(data_compra_str, "%Y-%m-%d")
            valor_parcela = valor_total / parcelas

            # Lógica da Data da Primeira Parcela
            meses_add = 1 if data_compra.day > dia_fech else 0
            data_base = data_compra + relativedelta(months=meses_add)
            
            if dia_venc < dia_fech and meses_add == 0:
                 data_base = data_base + relativedelta(months=1)
            
            try: data_primeira_fatura = data_base.replace(day=dia_venc)
            except: data_primeira_fatura = data_base.replace(day=28)

            for i in range(parcelas):
                vencimento_parcela = data_primeira_fatura + relativedelta(months=i)
                desc_final = f"{descricao} ({i+1}/{parcelas})" if parcelas > 1 else descricao
                
                novo_boleto_cartao = Boleto(
                    descricao=desc_final,
                    valor=valor_parcela,
                    data_vencimento=vencimento_parcela.strftime("%Y-%m-%d"),
                    id_categoria=id_categoria,
                    codigo_barras="",
                    banco_cartao=nome_cartao, # Liga ao cartão
                    status='pendente',
                    obs=f"Compra em {data_compra_str}"
                )
                self.dao_boleto.salvar(novo_boleto_cartao)

            return f"Sucesso! Compra de R$ {valor_total:.2f} em {parcelas}x no {nome_cartao}."
        except Exception as e:
            return f"Erro ao processar compra: {e}"

    # --- 3. GESTÃO DE FATURAS ---
    def listar_faturas_agrupadas(self) -> Dict[str, Dict]:
        todos = self.dao_boleto.listar_todos()
        pendentes = [b for b in todos if b.status == 'pendente' and b.banco_cartao]
        
        faturas = {} 
        for b in pendentes:
            chave_unica = f"{b.data_vencimento}_{b.banco_cartao}"
            
            if chave_unica not in faturas:
                try: dt_br = datetime.strptime(b.data_vencimento, "%Y-%m-%d").strftime("%d/%m/%Y")
                except: dt_br = b.data_vencimento

                faturas[chave_unica] = {
                    "data_sql": b.data_vencimento,
                    "vencimento_br": dt_br,
                    "banco": b.banco_cartao, 
                    "total": 0.0, 
                    "itens": []
                }
            
            faturas[chave_unica]["total"] += b.valor
            faturas[chave_unica]["itens"].append(b)

        return faturas

    def pagar_fatura_inteira(self, chave_unica: str, banco_pagador: str, valor_total: float) -> str:
        partes = chave_unica.split('_')
        data_alvo = partes[0]
        banco_alvo = partes[1] if len(partes) > 1 else ""

        todos = self.dao_boleto.listar_todos()
        
        itens_fatura = [
            b for b in todos 
            if b.status == 'pendente' 
            and b.data_vencimento == data_alvo 
            and b.banco_cartao == banco_alvo 
        ]

        if not itens_fatura: return "Erro: Fatura não encontrada."

        for b in itens_fatura:
            b.status = 'pago'
            self.dao_boleto.salvar(b) # Baixa a parcela = Libera Limite automaticamente (pois não é mais 'pendente')

        data_hoje = date.today().strftime("%Y-%m-%d")
        try: dt_br = datetime.strptime(data_alvo, "%Y-%m-%d").strftime("%d/%m")
        except: dt_br = data_alvo

        self.fin_service.registrar_gasto_manual(
            descricao=f"Fatura {banco_alvo} (Venc {dt_br})",
            valor=valor_total,
            id_categoria=10, 
            data_gasto=data_hoje,
            banco=banco_pagador,
            forma="Boleto"
        )

        return f"Fatura {banco_alvo} paga com sucesso! ({len(itens_fatura)} itens baixados)"