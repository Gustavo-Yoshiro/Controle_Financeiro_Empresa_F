from typing import List, Dict
from datetime import date, datetime

from Persistencia.Impl import BoletoImpl
from Persistencia.Entidades import Boleto
from Service.FinanceiroService import FinanceiroService
from Service.CategoriaService import CategoriaService 

class BoletoService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao_boleto = BoletoImpl()
        self.cat_service = CategoriaService() 
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    # --- 1. CADASTRO DE BOLETO COMUM ---
    def cadastrar_boleto(self, descricao: str, valor: float, vencimento: str, id_categoria: int = 2, codigo: str = "") -> str:
        """ Cadastra um boleto comum (Água, Luz, Internet) """
        novo = Boleto(
            descricao=descricao,
            valor=abs(valor),
            data_vencimento=vencimento,
            id_categoria=id_categoria,
            codigo_barras=codigo,
            banco_cartao=None, # Garante que não é cartão
            status='pendente'
        )
        self.dao_boleto.salvar(novo)
        return "Boleto agendado com sucesso."

    # --- 2. LISTAGEM E PAGAMENTO ---
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

    def pagar_boleto(self, id_boleto: int, banco_pagador: str) -> str:
        """ Paga um boleto individual e lança no caixa """
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
        """ Calcula total pendente APENAS de boletos comuns """
        todos = self.dao_boleto.listar_todos()
        # Filtra pendentes que NÃO são cartão
        total_pagar = sum(b.valor for b in todos if b.status == 'pendente' and not b.banco_cartao)
        return {"total_geral": total_pagar}

    # --- MÉTODOS ADM ---
    def admin_listar_todos(self) -> List[Boleto]:
        return self.dao_boleto.listar_todos()

    def admin_excluir(self, id_b: int) -> str:
        self.dao_boleto.deletar(id_b)
        return "Boleto excluído."