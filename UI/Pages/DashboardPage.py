import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, timedelta, datetime
import calendar

class DashboardPage:
    def __init__(self, relatorio_service, transporte_service, config_service):
        self.s_relatorio = relatorio_service
        self.s_transporte = transporte_service
        self.cfg = config_service

    def render(self):
        st.title("📊 Painel de Controle")
        st.caption("Visão da Saúde Financeira Real")

        # FILTROS
        with st.expander("🔍 Filtros e Período", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            
            periodo = c1.selectbox("Período", ["Este Mês", "Ano Atual", "Desde o Início"])
            hoje = date.today()
            
            if periodo == "Este Mês":
                dt_ini = date(hoje.year, hoje.month, 1)
                ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
                dt_fim = date(hoje.year, hoje.month, ultimo_dia)
            elif periodo == "Ano Atual":
                dt_ini = date(hoje.year, 1, 1)
                dt_fim = date(hoje.year, 12, 31) 
            else:
                dt_ini = date(2020, 1, 1) 
                dt_fim = date(hoje.year, 12, 31)

            lista_bancos = self.cfg.listar_bancos() or []
            bancos_sel = c2.multiselect("Bancos", lista_bancos)

            frota = []
            if hasattr(self.s_transporte, 'listar_frota_simples'):
                frota = self.s_transporte.listar_frota_simples()
            
            opcoes_veiculos = {"Todos": None}
            for v in frota:
                lbl = v.get('label', f"{v.get('modelo','?')} - {v.get('placa','?')}")
                opcoes_veiculos[lbl] = v.get('id') or v.get('id_veiculo')
            
            veiculo_nome = c3.selectbox("Veículo", list(opcoes_veiculos.keys()))
            id_veiculo_sel = opcoes_veiculos[veiculo_nome]
            
            acumular = c4.toggle("Considerar Passado", value=True)

        # BUSCA DE DADOS (ANTECIPADA)
        dados_brutos_extrato = self.s_relatorio.gerar_extrato(
            str(dt_ini), str(dt_fim), bancos_sel, None, id_veiculo_sel
        )

        #  CÁLCULO DA "VERDADE" 
        
        resumo_periodo = self.s_relatorio.get_resumo_periodo(str(dt_ini), str(dt_fim), ver_acumulado=acumular)

        dt_futuro = date(date.today().year + 10, 12, 31)
        resumo_total = self.s_relatorio.get_resumo_periodo("2000-01-01", str(dt_futuro), ver_acumulado=True)

        val_saldo = resumo_periodo.get('saldo', 0.0)
        
        val_contas_total = resumo_total.get('a_pagar_contas', 0.0)
        val_cartao_total = resumo_total.get('a_pagar_cartao', 0.0)
        val_divida_total = resumo_total.get('divida_total', val_contas_total + val_cartao_total)
        
        saldo_disponivel_real = val_saldo - val_divida_total

        st.divider()

        if saldo_disponivel_real < 0:
            msg_erro = f"""
            ### 🚨 SITUAÇÃO CRÍTICA
            O dinheiro na conta **JÁ TEM DONO**.
            \n**Faltam R$ {abs(saldo_disponivel_real):,.2f} para cobrir Contas, Cartões e Empréstimos.**
            """
            st.error(msg_erro, icon="🛑")
            
        elif saldo_disponivel_real < 1000: 
            msg_alerta = f"""
            ### ⚠️ ALERTA: MARGEM PEQUENA
            Após pagar todas as faturas e contas, sobrarão apenas **R$ {saldo_disponivel_real:,.2f}**.
            """
            st.warning(msg_alerta, icon="⚠️")
            
        else:
            msg_sucesso = f"""
            ### ✅ SAÚDE FINANCEIRA OK
            Temos **R$ {saldo_disponivel_real:,.2f}** livres após projetar todas as dívidas.
            """
            st.success(msg_sucesso, icon="✅")

        st.divider()

        #  METRICAS GERAIS (SALDO E DÍVIDAS)
        
        c_saldo, c_contas, c_cartao, c_real = st.columns(4)

        c_saldo.metric(
            label="💰 Saldo (Caixa)",
            value=f"R$ {val_saldo:,.2f}",
            help="Dinheiro disponível hoje nas contas."
        )

        c_contas.metric(
            label="📉 Contas & Boletos",
            value=f"R$ {val_contas_total:,.2f}",
            delta="-A Pagar",
            delta_color="inverse",
            help="Total de contas e empréstimos pendentes (inclui futuros)."
        )

        c_cartao.metric(
            label="💳 Faturas Cartão",
            value=f"R$ {val_cartao_total:,.2f}",
            delta="-Fatura Total",
            delta_color="inverse",
            help="Soma de todas as faturas e parcelas futuras em aberto."
        )

        c_real.metric(
            label="🏁 SALDO LIVRE REAL",
            value=f"R$ {saldo_disponivel_real:,.2f}",
            delta="Livre" if saldo_disponivel_real > 0 else "FALTA DINHEIRO",
            delta_color="normal" if saldo_disponivel_real > 0 else "inverse",
            help="Saldo - (Todas as Dívidas Futuras)."
        )

        st.divider()

        #  GRÁFICOS E EVOLUÇÃO
        
        c_graf, c_tab = st.columns([1, 1.5])

        with c_graf:
            tab_gastos, tab_dividas, tab_historico, tab_perf = st.tabs(["🍰 Gastos", "📉 Dívidas", "📈 Evolução", "🚚 Performance"])
            
            with tab_gastos:
                dados_pizza = self.s_relatorio.get_gastos_periodo_flex(str(dt_ini), str(dt_fim))
                if dados_pizza:
                    df_pizza = pd.DataFrame(dados_pizza)
                    with plt.rc_context({'text.color': 'white', 'axes.labelcolor': 'white'}):
                        fig, ax = plt.subplots(figsize=(4, 4))
                        colors = plt.get_cmap('Reds')(np.linspace(0.4, 0.9, len(df_pizza)))
                        wedges, texts, autotexts = ax.pie(
                            df_pizza['valor'], labels=df_pizza['categoria'], autopct='%1.0f%%', 
                            startangle=90, colors=colors, textprops={'fontsize': 10}
                        )
                        for text in texts: text.set_color('white')
                        for autotext in autotexts: autotext.set_color('white')
                        fig.patch.set_alpha(0.0); ax.patch.set_alpha(0.0)
                        st.pyplot(fig)
                else:
                    st.info("Sem gastos registrados.")

            with tab_dividas:
                total_dividas = val_cartao_total + val_contas_total
                if total_dividas > 0:
                    df_dividas = pd.DataFrame([
                        {"Tipo": "Fatura Cartão", "Valor": val_cartao_total},
                        {"Tipo": "Boletos/Contas", "Valor": val_contas_total}
                    ])
                    df_dividas = df_dividas[df_dividas["Valor"] > 0]
                    
                    st.caption("Visão Geral")
                    with plt.rc_context({'text.color': 'white', 'axes.labelcolor': 'white'}):
                        fig2, ax2 = plt.subplots(figsize=(3, 3))
                        colors_div = ['#8A2BE2', '#CD5C5C'] 
                        ax2.pie(
                            df_dividas['Valor'], labels=df_dividas['Tipo'], autopct='%1.0f%%', 
                            startangle=90, colors=colors_div, textprops={'fontsize': 8}
                        )
                        fig2.patch.set_alpha(0.0); ax2.patch.set_alpha(0.0)
                        st.pyplot(fig2)
                        
                    if hasattr(self.s_relatorio, 'dao_boleto'):
                        todos_pendentes = [b for b in self.s_relatorio.dao_boleto.listar_todos() if b.status == 'pendente']
                        if todos_pendentes:
                            st.divider()
                            st.caption("Onde vai o dinheiro (Categorias)")
                            cats = self.cfg.listar_categorias()
                            mapa_cats = {c['id']: c['nome'] for c in cats}
                            dados_cat = {}
                            for b in todos_pendentes:
                                nome_cat = mapa_cats.get(b.id_categoria, "Outros")
                                dados_cat[nome_cat] = dados_cat.get(nome_cat, 0.0) + b.valor
                            
                            df_cat_futuro = pd.DataFrame(list(dados_cat.items()), columns=['Categoria', 'Valor'])
                            st.dataframe(df_cat_futuro.sort_values('Valor', ascending=False).style.format({"Valor": "R$ {:,.2f}"}), hide_index=True, width='stretch')

            with tab_historico:
                if dados_brutos_extrato:
                    df_hist = pd.DataFrame(dados_brutos_extrato)
                    
                    df_hist['dt_obj'] = pd.to_datetime(df_hist['raw_date'])
                    
                    df_hist['mes_ano'] = df_hist['dt_obj'].dt.strftime('%Y-%m')
                    
                    df_chart = df_hist.pivot_table(
                        index='mes_ano', 
                        columns='tipo', 
                        values='valor', 
                        aggfunc='sum',
                        fill_value=0
                    )
                    
                    if 'Despesa' in df_chart.columns:
                        df_chart['Despesa'] = df_chart['Despesa'].abs()
                    
                    df_chart = df_chart.sort_index()
                    
                    st.caption("Entradas vs Saídas (Mês a Mês)")
                    
                    cores_grafico = []
                    if 'Receita' in df_chart.columns: cores_grafico.append("#3dd56d")
                    if 'Despesa' in df_chart.columns: cores_grafico.append("#ff4b4b")
                    
                    st.bar_chart(df_chart, color=cores_grafico)
                else:
                    st.info("Sem dados para histórico.")

            with tab_perf:
                titulo_perf = f"Performance: {veiculo_nome}" if id_veiculo_sel else "Performance Geral"
                st.caption(titulo_perf)
                
                if dados_brutos_extrato:
                    entradas_filtro = sum(d['valor'] for d in dados_brutos_extrato if d['valor'] > 0)
                    saidas_filtro = sum(d['valor'] for d in dados_brutos_extrato if d['valor'] < 0)
                    resultado_filtro = entradas_filtro + saidas_filtro
                    
                    c_p1, c_p2 = st.columns(2)
                    c_p1.metric("Entradas", f"R$ {entradas_filtro:,.2f}")
                    c_p2.metric("Saídas", f"R$ {abs(saidas_filtro):,.2f}")
                    
                    st.metric("Resultado Líquido", f"R$ {resultado_filtro:,.2f}", 
                            delta="Lucro" if resultado_filtro >= 0 else "Prejuízo")
                    
                    st.divider()
                    
                    despesas_filtro = [d for d in dados_brutos_extrato if d['valor'] < 0]
                    
                    if despesas_filtro:
                        st.caption("Detalhamento de Custos")
                        df_perf_cat = pd.DataFrame(despesas_filtro)
                        df_chart_perf = df_perf_cat.groupby('categoria')['valor'].sum().abs().reset_index()
                        df_chart_perf.columns = ['Categoria', 'Valor']
                        df_chart_perf = df_chart_perf.sort_values('Valor', ascending=False)
                        
                        with plt.rc_context({'text.color': 'white', 'axes.labelcolor': 'white'}):
                            fig_p, ax_p = plt.subplots(figsize=(4, 4))
                            colors = plt.get_cmap('Reds')(np.linspace(0.4, 0.9, len(df_chart_perf)))
                            
                            wedges, texts, autotexts = ax_p.pie(
                                df_chart_perf['Valor'], labels=df_chart_perf['Categoria'], autopct='%1.0f%%', 
                                startangle=90, colors=colors, textprops={'fontsize': 10}
                            )
                            for text in texts: text.set_color('white')
                            for autotext in autotexts: autotext.set_color('white')
                            fig_p.patch.set_alpha(0.0); ax_p.patch.set_alpha(0.0)
                            st.pyplot(fig_p)
                    else:
                        st.info("Sem despesas registradas para detalhar.")
                        
                else:
                    st.info("Sem movimentações para este filtro.")

        with c_tab:
            st.markdown("##### 🧾 Extrato Detalhado")
            
            if dados_brutos_extrato:
                df_show = pd.DataFrame(dados_brutos_extrato)
                colunas_desejadas = ['data', 'descricao', 'valor', 'banco', 'categoria']
                colunas_existentes = [c for c in colunas_desejadas if c in df_show.columns]
                
                df_show = df_show[colunas_existentes]
                df_show.columns = [c.capitalize() for c in colunas_existentes]

                def colorir_valor(val):
                    cor = "#ff4b4b" if val < 0 else "#3dd56d"
                    return f"color: {cor}; font-weight: bold"

                st.dataframe(
                    df_show.style.format({"Valor": "R$ {:,.2f}"}).map(colorir_valor, subset=['Valor']),
                    width='stretch',
                    height=350, 
                    hide_index=True
                )
            else:
                st.caption("Sem movimentações.")