from datetime import datetime, date
from typing import List, Dict
from Persistencia.Impl.BoletoImpl import BoletoImpl
from Persistencia.Impl.MovimentacaoImpl import MovimentacaoImpl
from Persistencia.Impl.CategoriaImpl import CategoriaImpl
from Persistencia.Entidades.Boleto import Boleto
from Persistencia.Entidades.Movimentacao import Movimentacao

class BoletoService:
    def __init__(self):
        self.dao_boleto = BoletoImpl()
        self.dao_movimentacao = MovimentacaoImpl()
        self.dao_categoria = CategoriaImpl()

    def cadastrar_boleto(self, descricao: str, valor: float, vencimento: str, id_categoria: int, codigo: str = "") -> str:
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

    def pagar_boleto(self, id_boleto: int, banco_pagador: str, data_pagamento: str = None) -> str:
        """
        1. Marca boleto como pago no banco X.
        2. Lança despesa no caixa.
        """
        boleto = self.dao_boleto.buscar_por_id(id_boleto)
        if not boleto:
            return "Erro: Boleto não encontrado."
            
        if boleto.status == 'pago':
            return "Erro: Boleto já consta como pago."

        # 1. Atualiza status no módulo de Boletos
        self.dao_boleto.registrar_pagamento(id_boleto, banco_pagador)

        # 2. Lança no Financeiro (Despesa)
        data_final = data_pagamento if data_pagamento else date.today().strftime("%Y-%m-%d")
        
        mov = Movimentacao(
            descricao=f"Pgto Boleto ({banco_pagador}): {boleto.descricao}",
            valor= boleto.valor * -1, # Negativo para sair do caixa
            data_movimento=data_final,
            id_categoria=boleto.id_categoria
        )
        self.dao_movimentacao.salvar(mov)
        
        return "Boleto pago e valor descontado do caixa."

    def listar_boletos_detalhados(self) -> List[Dict]:
        boletos = self.dao_boleto.listar_pendentes()
        categorias = self.dao_categoria.listar_todas()
        lista_final = []
        hoje = date.today()

        for b in boletos:
            nome_cat = next((c.nome for c in categorias if c.id_categoria == b.id_categoria), "Geral")
            
            # Cálculo de dias
            try:
                data_venc = datetime.strptime(b.data_vencimento, "%Y-%m-%d").date()
                delta = (data_venc - hoje).days
            except:
                delta = 0
                data_venc = hoje # Fallback
            
            # Visual
            if delta < 0:
                status_texto = f"VENCIDO HÁ {abs(delta)} DIAS"
                cor = "red"
                bg = "#ffcccc"
            elif delta == 0:
                status_texto = "VENCE HOJE"
                cor = "orange"
                bg = "#fff5cc"
            elif delta <= 3:
                status_texto = f"Vence em {delta} dias"
                cor = "orange"
                bg = "white"
            else:
                status_texto = f"Vence em {delta} dias"
                cor = "blue"
                bg = "white"

            lista_final.append({
                "id": b.id_boleto,
                "descricao": b.descricao,
                "valor": b.valor,
                "vencimento_br": data_venc.strftime("%d/%m/%Y"),
                "categoria": nome_cat,
                "status_texto": status_texto,
                "cor_status": cor,
                "bg_color": bg,
                "codigo": b.codigo_barras
            })
        
        return lista_final

    def calcular_totais(self) -> Dict:
        boletos = self.listar_boletos_detalhados()
        total_pagar = sum(b['valor'] for b in boletos)
        
        # Filtro simples para mês atual
        mes_atual = date.today().month
        total_mes = sum(b['valor'] for b in boletos if datetime.strptime(b['vencimento_br'], "%d/%m/%Y").month == mes_atual)

        return {
            "total_geral": total_pagar,
            "total_mes": total_mes
        }