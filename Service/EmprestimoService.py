from datetime import datetime, date
from dateutil.relativedelta import relativedelta 
from typing import List

from Persistencia.Impl import EmprestimoImpl
from Persistencia.Entidades import Emprestimo
from Service import FinanceiroService, BoletoService

class EmprestimoService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao = EmprestimoImpl()
        # Injeção ou Instanciação direta
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()
        self.bol_service = BoletoService(self.fin_service)

    # --- MÉTODOS DE USO GERAL (PARA A PAGE EMPRÉSTIMOS) ---

    def contratar_emprestimo(self, descricao: str, valor_pego: float, valor_parcela: float, 
                             qtd_parcelas: int, data_liberacao: str, banco: str) -> str:
        
        # 1. Salva o Contrato
        novo_emp = Emprestimo(
            descricao=descricao,
            valor_total=valor_pego,
            valor_parcela=valor_parcela,
            qtd_parcelas=qtd_parcelas,
            juros_mensal=0.0,
            data_inicio=data_liberacao,
            banco_origem=banco,
            status='ativo'
        )
        self.dao.salvar(novo_emp)

        # 2. Lança a Entrada do Dinheiro (Receita)
        self.fin_service.registrar_receita_manual(
            descricao=f"Entrada Empréstimo: {descricao}",
            valor=valor_pego,
            id_categoria=1, # 1 = Receita
            data=data_liberacao,
            banco=banco,
            forma="Transferência"
        )

        # 3. Gera as Parcelas no "Contas a Pagar" (Boletos Futuros)
        try:
            data_base = datetime.strptime(data_liberacao, "%Y-%m-%d")
        except:
            data_base = datetime.now()

        for i in range(qtd_parcelas):
            # Calcula data: +1 mês, +2 meses... (Usa dateutil para virar o ano corretamente)
            data_venc = data_base + relativedelta(months=+(i+1))
            data_fmt = data_venc.strftime("%Y-%m-%d")
            
            num_parcela = i + 1
            desc_parcela = f"Parc. {num_parcela}/{qtd_parcelas} - {descricao}"
            
            # Cadastra no BoletoService (Isso vai aparecer na tela de Boletos/Contas)
            self.bol_service.cadastrar_boleto(
                descricao=desc_parcela,
                valor=valor_parcela,
                vencimento=data_fmt,
                id_categoria=2, 
                codigo="" 
            )

        return f"Empréstimo de R$ {valor_pego:.2f} registrado! {qtd_parcelas} parcelas geradas em Contas a Pagar."

    def listar_emprestimos(self) -> List[Emprestimo]:
        return self.dao.listar_todos()

    # --- MÉTODOS DE ADMINISTRAÇÃO (PARA A PAGE CONFIGURAÇÕES) ---

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