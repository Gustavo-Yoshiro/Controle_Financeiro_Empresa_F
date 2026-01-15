import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, timedelta
import calendar

class DashboardPage:
    def __init__(self, relatorio_service, transporte_service, config_service):
        self.s_relatorio = relatorio_service
        self.s_transporte = transporte_service
        self.cfg = config_service

    def render(self):
        st.title("📊 Painel de Controle")
        st.caption("Visão da Saúde Financeira Real")

        # =====================================================================
        # 1. FILTROS
        # =====================================================================
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
                dt_ini = date(2023, 1, 1)
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

        # =====================================================================
        # 2. CÁLCULO DA "VERDADE"
        # =====================================================================
        
        # Busca 1: Dados do Período Selecionado (Para Saldo de Caixa e Gráficos)
        resumo_periodo = self.s_relatorio.get_resumo_periodo(str(dt_ini), str(dt_fim), ver_acumulado=acumular)

        # Busca 2: Dados TOTAIS FUTUROS (Para Dívida Real e Cards de Cartão)
        dt_futuro = date(date.today().year + 10, 12, 31)
        resumo_total = self.s_relatorio.get_resumo_periodo("2000-01-01", str(dt_futuro), ver_acumulado=True)

        # Para o Saldo em Conta, usamos o do período (ou acumulado até hoje)
        val_saldo = resumo_periodo.get('saldo', 0.0)
        
        # Para as Dívidas, usamos o TOTAL (incluindo parcelas de 2026, 2027...)
        val_contas_total = resumo_total.get('a_pagar_contas', 0.0)
        val_cartao_total = resumo_total.get('a_pagar_cartao', 0.0)
        
        val_divida_total = resumo_total.get('divida_total', val_contas_total + val_cartao_total)
        saldo_disponivel_real = val_saldo - val_divida_total

        st.divider()

        # Semáforo da Realidade
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

        # =====================================================================
        # 3. OS QUATRO GRANDES NÚMEROS
        # =====================================================================
        
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

        # =====================================================================
        # 4. GRÁFICOS (AGORA COM ABAS) E TABELA
        # =====================================================================
        
        c_graf, c_tab = st.columns([1, 1.5])

        with c_graf:
            # Abas para alternar entre "Passado" (Gastos) e "Futuro" (Dívidas)
            tab_gastos, tab_dividas = st.tabs(["🍰 Gastos Realizados", "📉 Dívidas Futuras"])
            
            # --- GRÁFICO 1: GASTOS (CAIXA) ---
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

            # --- GRÁFICO 2: DÍVIDAS (FUTURO) ---
            with tab_dividas:
                total_dividas = val_cartao_total + val_contas_total
                
                if total_dividas > 0:
                    # 1. Gráfico Macro (Cartão vs Boleto)
                    df_dividas = pd.DataFrame([
                        {"Tipo": "Fatura Cartão", "Valor": val_cartao_total},
                        {"Tipo": "Boletos/Contas", "Valor": val_contas_total}
                    ])
                    df_dividas = df_dividas[df_dividas["Valor"] > 0]
                    
                    st.caption("Visão Geral")
                    with plt.rc_context({'text.color': 'white', 'axes.labelcolor': 'white'}):
                        fig2, ax2 = plt.subplots(figsize=(3, 3))
                        colors_div = ['#8A2BE2', '#CD5C5C'] 
                        wedges, texts, autotexts = ax2.pie(
                            df_dividas['Valor'], labels=df_dividas['Tipo'], autopct='%1.0f%%', 
                            startangle=90, colors=colors_div, textprops={'fontsize': 8}
                        )
                        for text in texts: text.set_color('white')
                        for autotext in autotexts: autotext.set_color('white')
                        fig2.patch.set_alpha(0.0); ax2.patch.set_alpha(0.0)
                        st.pyplot(fig2)

                    # 2. NOVO: Gráfico Detalhado por Categoria
                    # Busca os boletos pendentes diretamente (usando o acesso ao DAO disponível)
                    if hasattr(self.s_relatorio, 'dao_boleto'):
                        todos_pendentes = [b for b in self.s_relatorio.dao_boleto.listar_todos() if b.status == 'pendente']
                        
                        if todos_pendentes:
                            st.divider()
                            st.caption("Por Categoria (Onde vai o dinheiro)")
                            
                            cats = self.cfg.listar_categorias()
                            mapa_cats = {c['id']: c['nome'] for c in cats}
                            
                            dados_cat = {}
                            for b in todos_pendentes:
                                nome_cat = mapa_cats.get(b.id_categoria, "Outros")
                                dados_cat[nome_cat] = dados_cat.get(nome_cat, 0.0) + b.valor
                            
                            df_cat_futuro = pd.DataFrame(list(dados_cat.items()), columns=['Categoria', 'Valor'])
                            df_cat_futuro = df_cat_futuro[df_cat_futuro['Valor'] > 0].sort_values('Valor', ascending=False)
                            
                            with plt.rc_context({'text.color': 'white', 'axes.labelcolor': 'white'}):
                                fig3, ax3 = plt.subplots(figsize=(4, 4))
                                colors_cat = plt.get_cmap('Set3')(np.linspace(0, 1, len(df_cat_futuro)))
                                
                                wedges, texts, autotexts = ax3.pie(
                                    df_cat_futuro['Valor'], labels=df_cat_futuro['Categoria'], autopct='%1.0f%%', 
                                    startangle=90, colors=colors_cat, textprops={'fontsize': 10}
                                )
                                for text in texts: text.set_color('white')
                                for autotext in autotexts: autotext.set_color('white')
                                fig3.patch.set_alpha(0.0); ax3.patch.set_alpha(0.0)
                                st.pyplot(fig3)

                    st.caption(f"Total Futuro: R$ {total_dividas:,.2f}")
                else:
                    st.success("Tudo pago! Sem dívidas futuras.")

        with c_tab:
            st.markdown("##### 🧾 Extrato do Período")
            dados_extrato = self.s_relatorio.gerar_extrato(
                data_inicio=str(dt_ini), 
                data_fim=str(dt_fim),
                filtro_bancos=bancos_sel if bancos_sel else None,
                filtro_veiculo=id_veiculo_sel
            )

            if dados_extrato:
                df_show = pd.DataFrame(dados_extrato)
                colunas_desejadas = ['data', 'descricao', 'valor', 'banco']
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