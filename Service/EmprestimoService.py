from datetime import datetime, date
from dateutil.relativedelta import relativedelta 
from typing import List

from Persistencia.Impl import EmprestimoImpl
from Persistencia.Entidades import Emprestimo
from Service import FinanceiroService, BoletoService

class EmprestimoService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao = EmprestimoImpl()
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()
        self.bol_service = BoletoService(self.fin_service)

    # --- MÉTODOS DE USO GERAL (PARA A PAGE EMPRÉSTIMOS) ---

    def contratar_emprestimo(self, descricao: str, valor_pego: float, valor_parcela: float, 
                             qtd_parcelas: int, data_liberacao: str, data_primeira_parcela: str, # <--- NOVA DATA
                             banco: str) -> str:
        
        # Cálculo do Total Real da Dívida (Com Juros)
        valor_divida_total = valor_parcela * qtd_parcelas

        # 1. Salva o Contrato (Entidade para controle de Dívida Total)
        novo_emp = Emprestimo(
            descricao=descricao,
            valor_total=valor_divida_total, # Salva o total com juros
            valor_parcela=valor_parcela,
            qtd_parcelas=qtd_parcelas,
            juros_mensal=0.0, # Pode implementar cálculo depois se quiser
            data_inicio=data_liberacao,
            data_primeira_parcela=data_primeira_parcela, # <--- SALVA A DATA DE CORTE
            banco_origem=banco,
            valor_pago=0.0,
            status='ativo'
        )
        self.dao.salvar(novo_emp)

        # 2. Lança a Entrada do Dinheiro (Receita no Caixa HOJE)
        self.fin_service.registrar_receita_manual(
            descricao=f"Entrada Empréstimo: {descricao}",
            valor=valor_pego, # Entra só o liquido que pegou
            id_categoria=1,   # 1 = Receita
            data=data_liberacao,
            banco=banco,
            forma="Transferência"
        )

        # 3. Gera as Parcelas no "Contas a Pagar" (Boletos Futuros)
        try:
            # A data base para os boletos é a da PRIMEIRA PARCELA
            data_base_pagto = datetime.strptime(data_primeira_parcela, "%Y-%m-%d")
        except:
            data_base_pagto = datetime.now()

        for i in range(qtd_parcelas):
            # Lógica de Vencimento:
            # i=0 (1ª parc) -> data_base + 0 meses = Data Primeira Parcela
            # i=1 (2ª parc) -> data_base + 1 mês
            data_venc = data_base_pagto + relativedelta(months=+i)
            data_fmt = data_venc.strftime("%Y-%m-%d")
            
            num_parcela = i + 1
            desc_parcela = f"Parc. {num_parcela}/{qtd_parcelas} - {descricao}"
            
            # Cadastra no BoletoService
            # Isso alimenta o "A Pagar (Mês)" do Dashboard automaticamente
            self.bol_service.cadastrar_boleto(
                descricao=desc_parcela,
                valor=valor_parcela,
                vencimento=data_fmt,
                id_categoria=2, # Supondo Categoria 2 = Despesa ou Empréstimo
                codigo="" 
            )

        return f"Empréstimo registrado! Dívida Total: R$ {valor_divida_total:.2f}. Entrada: R$ {valor_pego:.2f}."

    def listar_emprestimos(self) -> List[Emprestimo]:
        return self.dao.listar_todos()

    # --- MÉTODOS DE ADMINISTRAÇÃO ---

    def admin_editar(self, id_e: int, desc: str, total: float, st: str) -> str:
        e = self.dao.buscar_por_id(id_e)
        if e:
            e.descricao = desc
            e.valor_total = total
            e.status = st
            self.dao.salvar(e) 
            return "Empréstimo atualizado."
        return "Erro: Empréstimo não encontrado."

    def admin_excluir(self, id_e: int) -> str:
        self.dao.deletar(id_e)
        return "Empréstimo excluído."