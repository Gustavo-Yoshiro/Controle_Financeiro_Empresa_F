from typing import List, Dict
from datetime import date, datetime

from Persistencia.Impl import BoletoImpl, CategoriaImpl

from Persistencia.Entidades import Boleto

from Service.FinanceiroService import FinanceiroService

class BoletoService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao_boleto = BoletoImpl()
        self.dao_categoria = CategoriaImpl()
        # Permite injetar ou cria novo se não passado (para evitar erro cíclico se houver)
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    def cadastrar_boleto(self, descricao: str, valor: float, vencimento: str, id_categoria: int = 2, codigo: str = "") -> str:
        novo = Boleto(
            descricao=descricao,
            valor=abs(valor),
            data_vencimento=vencimento,
            id_categoria=id_categoria,
            codigo_barras=codigo,
            status='pendente'
        )
        self.dao_boleto.salvar(novo)
        return "Boleto agendado com sucesso."

    def pagar_boleto(self, id_boleto: int, banco_pagador: str) -> str:
        boleto = self.dao_boleto.buscar_por_id(id_boleto)
        if not boleto: return "Erro: Boleto não encontrado."
        if boleto.status == 'pago': return "Erro: Já pago."

        # 1. Atualiza Boleto
        self.dao_boleto.registrar_pagamento(id_boleto, banco_pagador)

        # 2. Lança no Financeiro
        # Usa data de hoje + hora atual (tratado no financeiro service)
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
        boletos = self.dao_boleto.listar_pendentes()
        categorias = self.dao_categoria.listar_todas()
        lista_final = []
        hoje = date.today()

        for b in boletos:
            # Busca o nome da categoria pelo ID (List comprehension segura)
            nome_cat = next((c.nome for c in categorias if c.id_categoria == b.id_categoria), "Geral")
            
            try:
                data_venc = datetime.strptime(b.data_vencimento, "%Y-%m-%d").date()
                delta = (data_venc - hoje).days
            except:
                delta = 0
                data_venc = hoje
            
            # Status Visual para o Front-end
            if delta < 0: status_texto = f"VENCIDO HÁ {abs(delta)} DIAS"
            elif delta == 0: status_texto = "VENCE HOJE"
            else: status_texto = f"Vence em {delta} dias"

            lista_final.append({
                "id": b.id_boleto,
                "descricao": b.descricao,
                "valor": b.valor,
                "categoria": nome_cat, 
                "vencimento_br": data_venc.strftime("%d/%m/%Y"),
                "status_texto": status_texto,
                "codigo": b.codigo_barras
            })
        
        return lista_final

    def calcular_totais(self) -> Dict:
        boletos = self.dao_boleto.listar_pendentes()
        total_pagar = sum(b.valor for b in boletos)
        return {"total_geral": total_pagar}

    # --- MÉTODOS DE ADMINISTRAÇÃO (PARA A PAGE CONFIGURAÇÕES) ---

    def admin_listar_todos(self) -> List[Boleto]:
        return self.dao_boleto.listar_todos()

    def admin_editar(self, id_b: int, desc: str, val: float, venc: str, st: str, banco: str) -> str:
        b = self.dao_boleto.buscar_por_id(id_b)
        if b:
            b.descricao = desc
            b.valor = val
            b.data_vencimento = venc
            b.status = st
            b.banco_pagamento = banco
            self.dao_boleto.salvar(b) # Salvar com ID faz update automaticamente (Smart Save)
            return "Boleto atualizado."
        return "Erro: Boleto não achado."

    def admin_excluir(self, id_b: int) -> str:
        self.dao_boleto.deletar(id_b)
        return "Boleto excluído."