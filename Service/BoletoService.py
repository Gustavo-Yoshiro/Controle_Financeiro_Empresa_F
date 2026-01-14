from typing import List, Dict
from datetime import date, datetime

from Persistencia.Impl import BoletoImpl
from Persistencia.Entidades import Boleto

# Importa os Services necessários
from Service.FinanceiroService import FinanceiroService
from Service.CategoriaService import CategoriaService 

class BoletoService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao_boleto = BoletoImpl()
        self.cat_service = CategoriaService() 
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    # --- 1. CADASTROS ---

    def cadastrar_compra_cartao(self, descricao: str, valor: float, vencimento: str, id_categoria: int, banco_cartao: str) -> str:
        """ Cadastra uma compra específica de Cartão de Crédito """
        novo = Boleto(
            descricao=descricao,
            valor=abs(valor),
            data_vencimento=vencimento,
            id_categoria=id_categoria,
            codigo_barras="",
            banco_cartao=banco_cartao, # <--- AQUI ESTÁ A MÁGICA: Grava o nome do banco (Nubank, Inter...)
            status='pendente'
        )
        self.dao_boleto.salvar(novo)
        return f"Compra lançada na fatura do {banco_cartao}!"

    def cadastrar_boleto(self, descricao: str, valor: float, vencimento: str, id_categoria: int = 2, codigo: str = "") -> str:
        """ Cadastra um boleto comum (Água, Luz, Internet) """
        novo = Boleto(
            descricao=descricao,
            valor=abs(valor),
            data_vencimento=vencimento,
            id_categoria=id_categoria,
            codigo_barras=codigo,
            banco_cartao=None, # <--- Boleto comum não tem cartão vinculado
            status='pendente'
        )
        self.dao_boleto.salvar(novo)
        return "Boleto agendado com sucesso."

    # --- 2. AGENDAMENTO DE FATURAS (Aba 2 da Tela) ---

    def listar_faturas_agrupadas(self) -> Dict[str, Dict]:
        """
        Agrupa todas as compras de cartão pendentes por Data e Banco.
        Retorna: { '2026-05-15_Nubank': { 'total': 1500.0, 'itens': [...] } }
        """
        todos = self.dao_boleto.listar_todos()
        pendentes = [b for b in todos if b.status == 'pendente']
        
        faturas = {} 

        for b in pendentes:
            # SE TIVER 'banco_cartao', É ITEM DE FATURA!
            if b.banco_cartao: 
                # Chave única para agrupar: DATA + BANCO
                chave_unica = f"{b.data_vencimento}_{b.banco_cartao}"
                
                if chave_unica not in faturas:
                    # Formata data para BR
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
        """ Paga todos os itens daquela fatura de uma vez só """
        # Desmonta a chave "2026-05-15_Nubank"
        partes = chave_unica.split('_')
        data_alvo = partes[0]
        banco_alvo = partes[1] if len(partes) > 1 else ""

        todos = self.dao_boleto.listar_todos()
        
        # Filtra os itens exatos dessa fatura
        itens_fatura = [
            b for b in todos 
            if b.status == 'pendente' 
            and b.data_vencimento == data_alvo 
            and b.banco_cartao == banco_alvo # <--- COMPARAÇÃO SEGURA PELA COLUNA
        ]

        if not itens_fatura: return "Erro: Fatura não encontrada."

        # 1. Baixa os itens individuais (para não aparecerem mais como pendentes)
        for b in itens_fatura:
            b.status = 'pago'
            self.dao_boleto.salvar(b)

        # 2. Gera UM ÚNICO lançamento no Extrato
        data_hoje = date.today().strftime("%Y-%m-%d")
        
        # Formata data para descrição bonita
        try: dt_br = datetime.strptime(data_alvo, "%Y-%m-%d").strftime("%d/%m")
        except: dt_br = data_alvo

        self.fin_service.registrar_gasto_manual(
            descricao=f"Fatura {banco_alvo} (Venc {dt_br})",
            valor=valor_total,
            id_categoria=10, # Supondo ID 10 = Pagamento de Fatura (ou use Geral)
            data_gasto=data_hoje,
            banco=banco_pagador,
            forma="Boleto"
        )

        return f"Fatura {banco_alvo} paga com sucesso! ({len(itens_fatura)} compras baixadas)"

    # --- 3. LISTAGEM DE BOLETOS COMUNS (Aba 1 da Tela) ---

    def listar_boletos_detalhados(self) -> List[Dict]:
        """ Lista apenas boletos que NÃO são de cartão de crédito """
        todos = self.dao_boleto.listar_todos()
        
        # FILTRO: Apenas pendentes E que NÃO têm banco_cartao
        boletos = [b for b in todos if b.status == 'pendente' and not b.banco_cartao]
        
        categorias = self.cat_service.listar_todas() 
        lista_final = []
        hoje = date.today()

        for b in boletos:
            nome_cat = next((c['nome'] for c in categorias if c['id'] == b.id_categoria), "Geral")
            
            try:
                data_venc = datetime.strptime(b.data_vencimento, "%Y-%m-%d").date()
                delta = (data_venc - hoje).days
            except:
                delta = 0
                data_venc = hoje
            
            if delta < 0: status_texto = f"⚠️ VENCIDO HÁ {abs(delta)} DIAS"
            elif delta == 0: status_texto = "📅 VENCE HOJE"
            else: status_texto = f"Em dia (Vence em {delta} dias)"

            lista_final.append({
                "id": b.id_boleto,
                "descricao": b.descricao,
                "valor": b.valor,
                "categoria": nome_cat, 
                "vencimento_br": data_venc.strftime("%d/%m/%Y"),
                "status_texto": status_texto,
                "status": b.status,
                "codigo_barras": b.codigo_barras 
            })
        
        lista_final.sort(key=lambda x: datetime.strptime(x['vencimento_br'], "%d/%m/%Y"))
        
        return lista_final

    # --- 4. PAGAMENTO INDIVIDUAL DE BOLETO ---

    def pagar_boleto(self, id_boleto: int, banco_pagador: str) -> str:
        boleto = self.dao_boleto.buscar_por_id(id_boleto)
        if not boleto: return "Erro: Boleto não encontrado."
        if boleto.status == 'pago': return "Erro: Já pago."

        # 1. Atualiza Boleto para Pago
        boleto.status = 'pago'
        self.dao_boleto.salvar(boleto)

        # 2. Lança a Saída no Financeiro
        data_hoje = date.today().strftime("%Y-%m-%d")
        
        self.fin_service.registrar_gasto_manual(
            descricao=f"Pgto Boleto: {boleto.descricao}",
            valor=boleto.valor,
            id_categoria=boleto.id_categoria,
            data_gasto=data_hoje,
            banco=banco_pagador,
            forma="Boleto"
        )
        return "Boleto pago e lançado no caixa."

    def calcular_totais(self) -> Dict:
        todos = self.dao_boleto.listar_todos()
        # Total geral = Boletos comuns + Compras de cartão pendentes
        total_pagar = sum(b.valor for b in todos if b.status == 'pendente')
        return {"total_geral": total_pagar}

    # --- MÉTODOS ADM ---
    def admin_listar_todos(self) -> List[Boleto]:
        return self.dao_boleto.listar_todos()

    def admin_excluir(self, id_b: int) -> str:
        self.dao_boleto.deletar(id_b)
        return "Boleto excluído."