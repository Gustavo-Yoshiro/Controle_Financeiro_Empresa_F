from typing import List, Dict
from datetime import datetime, date
import calendar
from Persistencia.Impl import MovimentacaoImpl, DividaVeiculoImpl, PagamentoAluguelImpl, PagamentoAlocacaoImpl, EmprestimoImpl, BoletoImpl
from Service.CategoriaService import CategoriaService 

class RelatorioFinanceiroService:
    def __init__(self, categoria_service: CategoriaService = None):
        self.dao = MovimentacaoImpl()
        self.cat_service = categoria_service if categoria_service else CategoriaService()
        
        self.dao_boleto = BoletoImpl()
        self.dao_divida_veiculo = DividaVeiculoImpl()
        self.dao_aluguel = PagamentoAluguelImpl()
        self.dao_alocacao = PagamentoAlocacaoImpl()
        self.dao_emprestimo = EmprestimoImpl()

    def get_resumo_periodo(self, data_inicio_str: str, data_fim_str: str, ver_acumulado: bool = True) -> Dict[str, float]:
        """
        Calcula os KPIs financeiros.
        A mágica acontece aqui: ele separa automaticamente o que é Cartão do que é Boleto
        apenas verificando se o campo 'banco_cartao' existe.
        """
        
        #  CAIXA REALIZADO 
        movs = self.dao.listar_periodo(data_inicio_str, data_fim_str)
        receitas_caixa = sum(m.valor for m in movs if m.valor > 0)
        despesas_caixa = sum(m.valor for m in movs if m.valor < 0)
        saldo_caixa = receitas_caixa + despesas_caixa

        #  PREVISÃO / DÍVIDAS 
        
        a_pagar_boletos = 0.0      
        a_pagar_cartao = 0.0       
        divida_total_geral = 0.0   
        
        for b in self.dao_boleto.listar_todos():
            if b.status == 'pendente':
                divida_total_geral += b.valor
                
                entra = False
                if ver_acumulado:
                    if b.data_vencimento and b.data_vencimento <= data_fim_str: entra = True
                else:
                    if b.data_vencimento and data_inicio_str <= b.data_vencimento <= data_fim_str: entra = True
                
                if entra:
                    if b.banco_cartao: 
                        a_pagar_cartao += b.valor 
                    else:
                        a_pagar_boletos += b.valor 

        for d in self.dao_divida_veiculo.listar_todas():
            if d.status == 'pendente':
                divida_total_geral += d.valor
                
                entra = False
                if ver_acumulado:
                    if d.data_vencimento and d.data_vencimento <= data_fim_str: entra = True
                else:
                    if d.data_vencimento and data_inicio_str <= d.data_vencimento <= data_fim_str: entra = True
                
                if entra: a_pagar_boletos += d.valor

        for e in self.dao_emprestimo.listar_todos():
            if e.status == 'ativo':
                restante = e.valor_total - e.valor_pago
                if restante > 0:
                    divida_total_geral += restante
                    a_pagar_boletos += restante

        a_receber_periodo = 0.0
        mes_ini_ref = data_inicio_str[:7]
        mes_fim_ref = data_fim_str[:7]

        for a in self.dao_aluguel.listar_todos():
            if a.status in ['pendente', 'atrasado', 'parcial']:
                entra = False
                if ver_acumulado:
                    if a.mes_referencia <= mes_fim_ref: entra = True
                else:
                    if mes_ini_ref <= a.mes_referencia <= mes_fim_ref: entra = True
                if entra: a_receber_periodo += (a.valor_esperado - a.valor_pago)

        for l in self.dao_alocacao.listar_todos():
            if l.status in ['pendente', 'atrasado', 'parcial']:
                entra = False
                if ver_acumulado:
                    if l.mes_referencia <= mes_fim_ref: entra = True
                else:
                    if mes_ini_ref <= l.mes_referencia <= mes_fim_ref: entra = True
                if entra: a_receber_periodo += (l.valor_esperado - l.valor_pago)

        total_a_pagar_periodo = a_pagar_boletos + a_pagar_cartao

        return {
            "receitas": receitas_caixa,
            "despesas": despesas_caixa,
            "saldo": saldo_caixa,
            
            "a_pagar_total": total_a_pagar_periodo, 
            "a_pagar_contas": a_pagar_boletos,      
            "a_pagar_cartao": a_pagar_cartao,       
            
            "divida_total": divida_total_geral,     
            
            "a_receber": a_receber_periodo,
            "previsao_final": saldo_caixa + a_receber_periodo - total_a_pagar_periodo
        }

    def gerar_extrato(self, data_inicio: str, data_fim: str, 
                      filtro_bancos: List[str] = None, 
                      filtro_formas: List[str] = None,
                      filtro_veiculo: int = None) -> List[Dict]:
        movimentacoes = self.dao.listar_periodo(data_inicio, data_fim)
        categorias = self.cat_service.listar_todas() 
        extrato = []
        for m in movimentacoes:
            if filtro_bancos and m.banco not in filtro_bancos: continue 
            if filtro_formas and m.forma_pagamento not in filtro_formas: continue
            if filtro_veiculo and m.id_veiculo != filtro_veiculo: continue

            nome_cat = next((c['nome'] for c in categorias if c['id'] == m.id_categoria), "Geral")
            
            data_fmt = str(m.data_movimento)
            try:
                dt_obj = datetime.strptime(data_fmt, "%Y-%m-%d %H:%M:%S")
                data_fmt = dt_obj.strftime("%d/%m/%Y %H:%M")
            except:
                try: dt_obj = datetime.strptime(data_fmt, "%Y-%m-%d"); data_fmt = dt_obj.strftime("%d/%m/%Y")
                except: pass

            extrato.append({
                "id": m.id_movimentacao, "data": data_fmt, "descricao": m.descricao,
                "categoria": nome_cat, "valor": m.valor,
                "tipo": "Receita" if m.valor > 0 else "Despesa",
                "banco": m.banco, "forma": m.forma_pagamento, "raw_date": m.data_movimento 
            })
        extrato.sort(key=lambda x: x['raw_date'], reverse=True)
        return extrato

    def get_gastos_periodo_flex(self, data_inicio: str, data_fim: str) -> List[Dict]:
        movs = self.dao.listar_periodo(data_inicio, data_fim)
        categorias = self.cat_service.listar_todas()
        agrupado = {}
        for m in movs:
            if m.valor < 0: 
                nome_cat = next((c['nome'] for c in categorias if c['id'] == m.id_categoria), "Outros")
                agrupado[nome_cat] = agrupado.get(nome_cat, 0) + abs(m.valor)
        return [{"categoria": k, "valor": v} for k, v in agrupado.items()]