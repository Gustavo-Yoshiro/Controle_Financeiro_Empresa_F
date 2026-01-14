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
        
        # Busca dados detalhados (agora vem separado cartão e boletos)
        resumo = self.s_relatorio.get_resumo_periodo(str(dt_ini), str(dt_fim), ver_acumulado=acumular)

        # A conta: Saldo - Tudo que devo (Boletos + Cartão + Empréstimos)
        # O campo 'divida_total' do service já soma tudo isso.
        saldo_disponivel_real = resumo['saldo'] - resumo['divida_total']

        st.divider()

        # Semáforo da Realidade
        if saldo_disponivel_real < 0:
            st.error(f"""
            ### 🚨 SITUAÇÃO CRÍTICA
            O dinheiro na conta **JÁ TEM DONO**.
            \n**Faltam R$ {abs(saldo_disponivel_real):,.2f} para cobrir Contas, Cartões e Empréstimos.**
            """, icon="🛑")
            
        elif saldo_disponivel_real < 1000: 
            st.warning(f"""
            ### ⚠️ ALERTA: MARGEM PEQUENA
            Após pagar todas as faturas e contas, sobrarão apenas **R$ {saldo_disponivel_real:,.2f}**.
            """, icon="⚠️")
            
        else:
            st.success(f"""
            ### ✅ SAÚDE FINANCEIRA OK
            Temos **R$ {saldo_disponivel_real:,.2f}** livres após projetar todas as dívidas.
            """, icon="✅")

        st.divider()

        # =====================================================================
        # 3. OS QUATRO GRANDES NÚMEROS (Visualização Detalhada)
        # =====================================================================
        
        # Agora usamos 4 colunas para separar Boleto de Cartão
        c_saldo, c_contas, c_cartao, c_real = st.columns(4)

        # 1. SALDO
        c_saldo.metric(
            label="💰 Saldo (Caixa)",
            value=f"R$ {resumo['saldo']:,.2f}",
            help="Dinheiro disponível hoje nas contas."
        )

        # 2. CONTAS FIXAS
        c_contas.metric(
            label="📉 Contas & Boletos",
            value=f"R$ {resumo['a_pagar_contas']:,.2f}", # Valor só dos boletos/empréstimos
            delta="-A Pagar",
            delta_color="inverse",
            help="Água, Luz, Internet, Empréstimos e Manutenções."
        )

        # 3. FATURAS DE CARTÃO (NOVO!)
        c_cartao.metric(
            label="💳 Faturas Cartão",
            value=f"R$ {resumo['a_pagar_cartao']:,.2f}", # Valor só do cartão
            delta="-Fatura",
            delta_color="inverse",
            help="Soma de todas as compras no crédito pendentes."
        )

        # 4. SALDO REAL
        c_real.metric(
            label="🏁 SALDO LIVRE REAL",
            value=f"R$ {saldo_disponivel_real:,.2f}",
            delta="Livre" if saldo_disponivel_real > 0 else "FALTA DINHEIRO",
            delta_color="normal" if saldo_disponivel_real > 0 else "inverse",
            help="Saldo - (Contas + Cartões + Dívidas Totais)."
        )

        # =====================================================================
        # 4. GRÁFICO E TABELA
        # =====================================================================
        
        c_graf, c_tab = st.columns([1, 1.5])

        with c_graf:
            st.markdown("##### 🍰 Gastos do Período")
            dados_pizza = self.s_relatorio.get_gastos_periodo_flex(str(dt_ini), str(dt_fim))
            
            if dados_pizza:
                df_pizza = pd.DataFrame(dados_pizza)
                with plt.rc_context({'text.color': 'white', 'axes.labelcolor': 'white'}):
                    fig, ax = plt.subplots(figsize=(4, 4))
                    # Cores avermelhadas para indicar gastos
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
                df_show = df_show[['data', 'descricao', 'valor', 'banco']]
                df_show.columns = ['Data', 'Descrição', 'Valor', 'Banco']

                def colorir_valor(val):
                    return f'color: {"#ff4b4b" if val < 0 else "#3dd56d"}; font-weight: bold'

                st.dataframe(
                    df_show.style.format({"Valor": "R$ {:,.2f}"}).map(colorir_valor, subset=['Valor']),
                    width=None, # Ajuste automático
                    height=350, 
                    hide_index=True
                )
            else:
                st.caption("Sem movimentações.")