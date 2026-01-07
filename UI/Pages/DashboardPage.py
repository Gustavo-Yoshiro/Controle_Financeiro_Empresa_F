import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, timedelta

class DashboardPage:
    def __init__(self, relatorio_service, transporte_service, config_service):
        self.s_relatorio = relatorio_service
        self.s_transporte = transporte_service
        self.cfg = config_service

    def render(self):
        st.title("📊 Dashboard Financeiro")

        # =====================================================================
        # 1. ÁREA DE FILTROS
        # =====================================================================
        with st.expander("🔍 Filtros de Visualização", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            
            # Filtro de Período
            periodo = c1.selectbox("Período", ["Este Mês", "Ano Atual", "Desde o Início", "Personalizado"])
            
            hoje = date.today()
            if periodo == "Este Mês":
                dt_ini = date(hoje.year, hoje.month, 1)
                dt_fim = hoje
            elif periodo == "Ano Atual":
                dt_ini = date(hoje.year, 1, 1)
                dt_fim = hoje
            elif periodo == "Desde o Início":
                dt_ini = date(2023, 1, 1)
                dt_fim = hoje
            else:
                dt_ini = c1.date_input("Início", value=hoje - timedelta(days=30))
                dt_fim = c1.date_input("Fim", value=hoje)

            # Filtro de Banco
            lista_bancos = self.cfg.listar_bancos() or []
            bancos_sel = c2.multiselect("Filtrar Banco", lista_bancos)

            # Filtro de Veículo
            # Funciona tanto com TransporteService quanto com FrotaService
            frota = self.s_transporte.listar_frota_simples() if self.s_transporte else []
            
            opcoes_veiculos = {"Todos": None}
            for v in frota:
                # O Service retorna dicts com 'id', 'modelo', 'placa' (TransporteService)
                # ou 'id', 'label' (FrotaService). Vamos garantir compatibilidade:
                if 'label' in v:
                    label = v['label']
                else:
                    label = f"{v.get('modelo','?')} - {v.get('placa','?')}"
                
                opcoes_veiculos[label] = v.get('id')
            
            veiculo_nome = c3.selectbox("Filtrar Veículo", list(opcoes_veiculos.keys()))
            id_veiculo_sel = opcoes_veiculos[veiculo_nome]

        # =====================================================================
        # 2. BUSCA DE DADOS
        # =====================================================================
        
        # O RelatorioFinanceiroService já sabe filtrar e formatar
        dados_extrato = self.s_relatorio.gerar_extrato(
            data_inicio=str(dt_ini),
            data_fim=str(dt_fim),
            filtro_bancos=bancos_sel if bancos_sel else None,
            filtro_veiculo=id_veiculo_sel
        )

        # Cálculo de KPIs (Feito na memória)
        total_receitas = sum(d['valor'] for d in dados_extrato if d['valor'] > 0)
        total_despesas = sum(d['valor'] for d in dados_extrato if d['valor'] < 0)
        saldo = total_receitas + total_despesas

        # =====================================================================
        # 3. EXIBIÇÃO DOS KPIS
        # =====================================================================
        
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("Saldo do Período", f"R$ {saldo:,.2f}")
        col2.metric("Receitas", f"R$ {total_receitas:,.2f}", delta="Entradas")
        col3.metric("Despesas", f"R$ {total_despesas:,.2f}", delta="Saídas", delta_color="inverse")

        # =====================================================================
        # 4. GRÁFICOS E TABELAS
        # =====================================================================
        
        c_graf, c_tab = st.columns([1, 2])

        with c_graf:
            st.subheader("Gastos por Categoria")
            if dados_extrato:
                df = pd.DataFrame(dados_extrato)
                # Filtra apenas despesas
                df_despesas = df[df['valor'] < 0].copy()
                
                if not df_despesas.empty:
                    df_despesas['valor_abs'] = df_despesas['valor'].abs()
                    gastos_cat = df_despesas.groupby('categoria')['valor_abs'].sum()
                    
                    # --- PLOT PIE CHART ---
                    # Contexto para garantir cor branca nos textos (Dark Mode)
                    with plt.rc_context({'text.color': 'white', 'axes.labelcolor': 'white'}):
                        fig, ax = plt.subplots(figsize=(4, 4))
                        
                        colors = plt.get_cmap('Set3')(np.linspace(0, 1, len(gastos_cat)))
                        
                        wedges, texts, autotexts = ax.pie(
                            gastos_cat, 
                            labels=gastos_cat.index, 
                            autopct='%1.0f%%', 
                            startangle=90, 
                            colors=colors,
                            textprops={'fontsize': 9}
                        )
                        
                        # Ajuste visual
                        for text in texts: text.set_color('white')
                        for autotext in autotexts: autotext.set_color('black')

                        # Fundo Transparente
                        fig.patch.set_alpha(0.0)
                        ax.patch.set_alpha(0.0)

                        st.pyplot(fig)
                else:
                    st.info("Sem despesas no período.")
            else:
                st.warning("Sem dados.")

        with c_tab:
            st.subheader("Últimos Lançamentos")
            if dados_extrato:
                df_show = pd.DataFrame(dados_extrato)
                df_show = df_show[['data', 'descricao', 'categoria', 'valor']]
                
                st.dataframe(
                    df_show.style.format({"valor": "R$ {:.2f}"}),
                    width="stretch", 
                    height=400,
                    hide_index=True
                )
            else:
                st.caption("Nenhum registro encontrado.")