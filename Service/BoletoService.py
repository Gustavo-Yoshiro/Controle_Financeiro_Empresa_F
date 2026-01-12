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
        
        # Instancia sua CategoriaService
        self.cat_service = CategoriaService() 
        
        # Instancia FinanceiroService (com proteção contra loop de importação)
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    def cadastrar_boleto(self, descricao: str, valor: float, vencimento: str, id_categoria: int = 2, codigo: str = "") -> str:
        novo = Boleto(
            descricao=descricao,
            valor=abs(valor),
            data_vencimento=vencimento,
            id_categoria=id_categoria,
            codigo_barras=codigo, # Salva o código que veio da tela
            status='pendente'
        )
        self.dao_boleto.salvar(novo)
        return "Boleto agendado com sucesso."

    def pagar_boleto(self, id_boleto: int, banco_pagador: str) -> str:
        boleto = self.dao_boleto.buscar_por_id(id_boleto)
        if not boleto: return "Erro: Boleto não encontrado."
        if boleto.status == 'pago': return "Erro: Já pago."

        # 1. Atualiza Boleto para Pago
        boleto.status = 'pago'
        self.dao_boleto.salvar(boleto)

        # 2. Lança a Saída no Financeiro (Caixa)
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

    def listar_boletos_detalhados(self) -> List[Dict]:
        """ Prepara os dados para exibir na DividasPage """
        
        # 1. Busca pendentes do banco
        todos = self.dao_boleto.listar_todos()
        boletos = [b for b in todos if b.status == 'pendente']
        
        # 2. Busca categorias (retorna List[Dict] conforme seu código)
        categorias = self.cat_service.listar_todas() 
        
        lista_final = []
        hoje = date.today()

        for b in boletos:
            # Cruza ID para pegar o Nome da Categoria
            # Como categorias é lista de dicts [{'id':1, 'nome':'X'}], acessamos assim:
            nome_cat = next((c['nome'] for c in categorias if c['id'] == b.id_categoria), "Geral")
            
            # Cálculo de Dias Restantes
            try:
                data_venc = datetime.strptime(b.data_vencimento, "%Y-%m-%d").date()
                delta = (data_venc - hoje).days
            except:
                delta = 0
                data_venc = hoje
            
            # Define Texto do Status
            if delta < 0: status_texto = f"⚠️ VENCIDO HÁ {abs(delta)} DIAS"
            elif delta == 0: status_texto = "📅 VENCE HOJE"
            else: status_texto = f"Em dia (Vence em {delta} dias)"

            # Monta o Dicionário para a UI
            lista_final.append({
                "id": b.id_boleto,
                "descricao": b.descricao,
                "valor": b.valor,
                "categoria": nome_cat, 
                "vencimento_br": data_venc.strftime("%d/%m/%Y"),
                "status_texto": status_texto,
                "status": b.status,
                
                # AQUI ESTÁ A CHAVE CERTA PARA O ST.CODE:
                "codigo_barras": b.codigo_barras 
            })
        
        # Ordena por vencimento (mais urgentes primeiro)
        lista_final.sort(key=lambda x: datetime.strptime(x['vencimento_br'], "%d/%m/%Y"))
        
        return lista_final

    def calcular_totais(self) -> Dict:
        todos = self.dao_boleto.listar_todos()
        total_pagar = sum(b.valor for b in todos if b.status == 'pendente')
        return {"total_geral": total_pagar}

    # --- MÉTODOS ADM ---
    def admin_listar_todos(self) -> List[Boleto]:
        return self.dao_boleto.listar_todos()

    def admin_excluir(self, id_b: int) -> str:
        self.dao_boleto.deletar(id_b)
        return "Boleto excluído."