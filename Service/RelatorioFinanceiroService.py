from typing import List, Dict
from datetime import datetime
import calendar # Essencial para saber se o mês acaba dia 30, 31 ou 28

from Persistencia.Impl import MovimentacaoImpl
from Service import CategoriaService 

class RelatorioFinanceiroService:
    def __init__(self, categoria_service: CategoriaService = None):
        self.dao = MovimentacaoImpl()
        # Injeção opcional
        self.cat_service = categoria_service if categoria_service else CategoriaService()

    def get_resumo_mes(self, mes: int, ano: int) -> Dict[str, float]:
        """Calcula totais para os Cards do topo do Dashboard"""
        
        # Lógica segura para pegar do dia 1 até o último dia do mês
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        data_inicio = f"{ano}-{mes:02d}-01"
        data_fim = f"{ano}-{mes:02d}-{ultimo_dia}"
        
        movs = self.dao.listar_periodo(data_inicio, data_fim)
        
        receitas = sum(m.valor for m in movs if m.valor > 0)
        despesas = sum(m.valor for m in movs if m.valor < 0)
        
        return {
            "receitas": receitas, 
            "despesas": despesas, 
            "saldo": receitas + despesas
        }

    def gerar_extrato(self, data_inicio: str, data_fim: str, 
                      filtro_bancos: List[str] = None, 
                      filtro_formas: List[str] = None,
                      filtro_veiculo: int = None) -> List[Dict]:
        """Gera os dados para a Tabela detalhada (Grid)"""
        
        movimentacoes = self.dao.listar_periodo(data_inicio, data_fim)
        categorias = self.cat_service.listar_todas() # Retorna lista de dicts
        
        extrato = []
        for m in movimentacoes:
            # Filtros em memória (Python)
            if filtro_bancos and m.banco not in filtro_bancos: continue 
            if filtro_formas and m.forma_pagamento not in filtro_formas: continue
            if filtro_veiculo and m.id_veiculo != filtro_veiculo: continue

            # Busca nome da categoria (Safety check com next)
            nome_cat = next((c['nome'] for c in categorias if c['id'] == m.id_categoria), "Geral")
            
            # Formata data para visualização BR (DD/MM/YYYY HH:MM)
            data_fmt = m.data_movimento
            try:
                # Tenta formatar se vier com hora
                dt_obj = datetime.strptime(str(m.data_movimento), "%Y-%m-%d %H:%M:%S")
                data_fmt = dt_obj.strftime("%d/%m/%Y %H:%M")
            except:
                try:
                    # Tenta formatar se vier só data
                    dt_obj = datetime.strptime(str(m.data_movimento), "%Y-%m-%d")
                    data_fmt = dt_obj.strftime("%d/%m/%Y")
                except:
                    pass

            extrato.append({
                "id": m.id_movimentacao,
                "data": data_fmt,
                "descricao": m.descricao,
                "categoria": nome_cat,
                "valor": m.valor,
                "tipo": "Receita" if m.valor > 0 else "Despesa",
                "banco": m.banco,
                "forma": m.forma_pagamento,
                # Dados ocultos úteis para lógica de front
                "raw_date": m.data_movimento 
            })
        
        # Ordena por data (mais recente primeiro)
        extrato.sort(key=lambda x: x['raw_date'], reverse=True)
        return extrato

    def get_gastos_por_categoria(self, mes: int, ano: int) -> List[Dict]:
        """Prepara dados para o Gráfico de Pizza (Despesas por Categoria)"""
        
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        data_inicio = f"{ano}-{mes:02d}-01"
        data_fim = f"{ano}-{mes:02d}-{ultimo_dia}"
        
        movs = self.dao.listar_periodo(data_inicio, data_fim)
        categorias = self.cat_service.listar_todas()
        
        # Dicionário acumulador: { 'Alimentação': 500.00, 'Lazer': 200.00 }
        agrupado = {}
        
        for m in movs:
            if m.valor < 0: # Apenas despesas
                nome_cat = next((c['nome'] for c in categorias if c['id'] == m.id_categoria), "Outros")
                val_abs = abs(m.valor)
                if nome_cat in agrupado:
                    agrupado[nome_cat] += val_abs
                else:
                    agrupado[nome_cat] = val_abs
                    
        # Converte para lista de dicts para o gráfico
        return [{"categoria": k, "valor": v} for k, v in agrupado.items()]