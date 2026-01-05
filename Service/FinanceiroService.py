from typing import List, Dict
from datetime import date, datetime
from Persistencia.Impl import MovimentacaoImpl
from Persistencia.Impl import CategoriaImpl
from Persistencia.Impl import PagamentoAluguelImpl
from Persistencia.Impl import PagamentoAlocacaoImpl
from Persistencia.Entidades.Movimentacao import Movimentacao

class FinanceiroService:
    def __init__(self):
        self.dao_movimentacao = MovimentacaoImpl()
        self.dao_categoria = CategoriaImpl()
        self.dao_pag_aluguel = PagamentoAluguelImpl()
        self.dao_pag_alocacao = PagamentoAlocacaoImpl()

    # =========================================================================
    # PARTE 1: TRANSAÇÕES (Atualizado com Banco e Forma de Pagamento)
    # =========================================================================

    def registrar_gasto_manual(self, descricao: str, valor: float, id_categoria: int, 
                               data_gasto: str = None, banco: str = "Não Inf.", forma: str = "Outro") -> str:
        """
        Registra despesa com os novos campos de rastreabilidade.
        """
        if valor > 0:
            valor = valor * -1 # Garante negativo
            
        data_final = data_gasto if data_gasto else date.today().strftime("%Y-%m-%d")

        nova_mov = Movimentacao(
            descricao=descricao,
            valor=valor,
            data_movimento=data_final,
            id_categoria=id_categoria,
            banco=banco,              # <--- Novo
            forma_pagamento=forma     # <--- Novo
        )
        self.dao_movimentacao.salvar(nova_mov)
        return "Sucesso: Despesa registrada."

    def registrar_receita_manual(self, descricao: str, valor: float, id_categoria: int, 
                                 data_receita: str = None, banco: str = "Não Inf.", forma: str = "Outro") -> str:
        """
        Registra receita com os novos campos.
        """
        if valor < 0:
            valor = valor * -1 # Garante positivo
            
        data_final = data_receita if data_receita else date.today().strftime("%Y-%m-%d")

        nova_mov = Movimentacao(
            descricao=descricao,
            valor=valor,
            data_movimento=data_final,
            id_categoria=id_categoria,
            banco=banco,              # <--- Novo
            forma_pagamento=forma     # <--- Novo
        )
        self.dao_movimentacao.salvar(nova_mov)
        return "Sucesso: Receita registrada."

    def receber_aluguel(self, id_pagamento: int, valor_recebido: float, banco_destino: str = "Caixa") -> str:
        """
        Baixa o aluguel e lança no caixa (Agora pedindo o banco).
        """
        pagamento = self.dao_pag_aluguel.buscar_por_id(id_pagamento)
        
        if not pagamento:
            return "Erro: Boleto não encontrado."
        if pagamento.status == 'pago':
            return "Erro: Já pago."

        # 1. Baixa no módulo imobiliário
        pagamento.status = 'pago'
        pagamento.valor_pago = valor_recebido
        pagamento.data_pagamento = date.today().strftime("%Y-%m-%d")
        self.dao_pag_aluguel.atualizar(pagamento)

        # 2. Lança no Financeiro
        nova_movimentacao = Movimentacao(
            descricao=f"Recebimento Aluguel - Ref: {pagamento.mes_referencia}",
            valor=valor_recebido,
            data_movimento=date.today().strftime("%Y-%m-%d"),
            id_categoria=1, # ID fixo para Aluguel (ajuste conforme seu banco)
            id_pagamento_aluguel=pagamento.id_aluguel,
            banco=banco_destino,           # <--- Novo
            forma_pagamento="Boleto/Pix"   # <--- Novo
        )
        self.dao_movimentacao.salvar(nova_movimentacao)

        return f"Sucesso: Aluguel recebido no banco {banco_destino}."

    # =========================================================================
    # PARTE 2: DASHBOARD
    # =========================================================================

    def get_resumo_mes(self, mes: int, ano: int) -> Dict[str, float]:
        data_inicio = f"{ano}-{mes:02d}-01"
        if mes == 12:
            data_fim = f"{ano+1}-01-01"
        else:
            data_fim = f"{ano}-{mes+1:02d}-01"

        # Usa o método listar_periodo que consertamos no DAO
        movimentacoes = self.dao_movimentacao.listar_periodo(data_inicio, data_fim)
        
        receitas = sum(m.valor for m in movimentacoes if m.valor > 0)
        despesas = sum(m.valor for m in movimentacoes if m.valor < 0)

        return {"receitas": receitas, "despesas": despesas, "saldo": receitas + despesas}

    def get_gastos_por_categoria(self, mes: int, ano: int) -> Dict[str, float]:
        data_inicio = f"{ano}-{mes:02d}-01"
        if mes == 12:
            data_fim = f"{ano+1}-01-01"
        else:
            data_fim = f"{ano}-{mes+1:02d}-01"

        movimentacoes = self.dao_movimentacao.listar_periodo(data_inicio, data_fim)
        todas_categorias = self.dao_categoria.listar_todas()
        
        resultado = {}
        for mov in movimentacoes:
            if mov.valor < 0:
                nome_cat = next((c.nome for c in todas_categorias if c.id_categoria == mov.id_categoria), "Geral")
                valor_positivo = abs(mov.valor)
                
                if nome_cat in resultado:
                    resultado[nome_cat] += valor_positivo
                else:
                    resultado[nome_cat] = valor_positivo
        return resultado

    # =========================================================================
    # PARTE 3: RELATÓRIOS E FILTROS (Atualizado)
    # =========================================================================

    def gerar_extrato_detalhado(self, data_inicio: str, data_fim: str, 
                                filtro_bancos: List[str] = None, 
                                filtro_formas: List[str] = None) -> List[Dict]:
        """
        Gera extrato aplicando filtros de Banco e Forma de Pagamento.
        """
        movimentacoes = self.dao_movimentacao.listar_periodo(data_inicio, data_fim)
        categorias = self.dao_categoria.listar_todas()
        
        extrato = []
        for m in movimentacoes:
            # --- Lógica de Filtro ---
            if filtro_bancos and m.banco not in filtro_bancos:
                continue # Pula se não for do banco selecionado
            if filtro_formas and m.forma_pagamento not in filtro_formas:
                continue # Pula se não for a forma selecionada

            nome_cat = next((c.nome for c in categorias if c.id_categoria == m.id_categoria), "-")
            tipo = "Receita" if m.valor > 0 else "Despesa"
            
            extrato.append({
                "id": m.id_movimentacao,
                "data": m.data_movimento,
                "descricao": m.descricao,
                "categoria": nome_cat,
                "valor": m.valor,
                "tipo": tipo,
                "banco": m.banco,               # <--- Retorna para a UI
                "forma_pagamento": m.forma_pagamento # <--- Retorna para a UI
            })
            
        return extrato
    
    def registrar_despesa_veiculo(self, descricao: str, valor: float, id_veiculo: int, 
                                  data_gasto: str, banco: str, forma: str) -> str:
        """
        Registra um gasto específico de veículo (Vincula o ID do carro).
        """
        if valor > 0:
            valor = valor * -1 # Garante negativo
            
        nova_mov = Movimentacao(
            descricao=descricao,
            valor=valor,
            data_movimento=data_gasto,
            id_categoria=3, # Supondo que ID 3 seja "Despesa com Veículos"
            banco=banco,
            forma_pagamento=forma,
            id_veiculo=id_veiculo # <--- O PULO DO GATO: Vínculo com a frota
        )
        self.dao_movimentacao.salvar(nova_mov)
        return "Manutenção/Despesa registrada com sucesso!"
    
    def listar_todas_categorias(self) -> List[Dict]:
        """
        Retorna todas as categorias para preencher os SelectBoxes da UI.
        """
        cats = self.dao_categoria.listar_todas()
        lista = []
        for c in cats:
            lista.append({
                "id": c.id_categoria,
                "nome": c.nome,
                "tipo": c.tipo # 'receita' ou 'despesa'
            })
        return lista