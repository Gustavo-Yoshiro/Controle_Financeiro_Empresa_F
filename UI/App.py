import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, date

# --- Importação dos Serviços ---
from Service.FinanceiroService import FinanceiroService
from Service.KitnetService import KitnetService
from Service.TransporteService import TransporteService
from Service.BoletoService import BoletoService
from Service.PixService import PixService

class AppInterface:
    def __init__(self):
        # Instancia os serviços (que carregam o banco automaticamente)
        self.fin = FinanceiroService()
        self.kit = KitnetService()
        self.trans = TransporteService()
        self.bol = BoletoService()
        self.pix = PixService()
        
        # Opções globais para SelectBoxes
        self.bancos_opcoes = ["Nubank", "Inter", "Caixa", "Brasil", "Santander", "Itaú", "Dinheiro", "Cofre"]
        self.formas_opcoes = ["Pix", "Débito", "Crédito", "Dinheiro", "Transferência", "Boleto"]

        self._configurar_estilo()

    def _configurar_estilo(self):
        # Pequeno ajuste CSS para métricas ficarem bonitas
        st.markdown("""
        <style>
            div[data-testid="stMetric"] {
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        </style>
        """, unsafe_allow_html=True)

    def executar(self):
        with st.sidebar:
            st.header("💎 Gestão Enterprise")
            # Menu lateral (Transações primeiro)
            menu_opcao = st.radio(
                "Navegação:",
                ["Transações", "Dashboard", "Kitnets", "Veículos", "Boletos", "Meus Pix"]
            )
            st.divider()
            st.caption("Sistema Integrado v3.2")

        # Roteamento
        if menu_opcao == "Transações":
            self._render_transacoes()
        elif menu_opcao == "Dashboard":
            self._render_dashboard()
        elif menu_opcao == "Kitnets":
            self._render_kitnets()
        elif menu_opcao == "Veículos":
            self._render_veiculos()
        elif menu_opcao == "Boletos":
            self._render_boletos()
        elif menu_opcao == "Meus Pix":
            self._render_pix()

    # ==========================================================================
    # 1. TRANSAÇÕES (Com Selectbox de Categorias)
    # ==========================================================================
    def _render_transacoes(self):
        st.title("📝 Transações Financeiras")
        
        # 1. Busca Categorias no Banco (Método novo do Service)
        # Se der erro aqui, verifique se criou o método listar_todas_categorias no FinanceiroService
        try:
            todas_cats = self.fin.listar_todas_categorias()
        except AttributeError:
            st.error("Erro: Método 'listar_todas_categorias' não encontrado no FinanceiroService.")
            todas_cats = []

        # 2. Separa e Mapeia: { "Nome": ID }
        opcoes_receita = {c['nome']: c['id'] for c in todas_cats if c['tipo'] == 'receita'}
        opcoes_despesa = {c['nome']: c['id'] for c in todas_cats if c['tipo'] == 'despesa'}

        # Fallback caso o banco esteja vazio
        if not opcoes_receita: opcoes_receita = {"Geral (Sem Categoria)": 1}
        if not opcoes_despesa: opcoes_despesa = {"Geral (Sem Categoria)": 2}

        c1, c2 = st.columns(2)
        
        # --- Form Receita ---
        with c1:
            with st.expander("➕ Nova Receita", expanded=False):
                with st.form("form_rec"):
                    desc = st.text_input("Descrição")
                    val = st.number_input("Valor (R$)", min_value=0.01)
                    
                    # Selectbox de Categorias (Receita)
                    nome_cat = st.selectbox("Categoria", list(opcoes_receita.keys()))
                    cat_id = opcoes_receita[nome_cat]

                    dt = st.date_input("Data", value=date.today())
                    banco = st.selectbox("Conta Destino", self.bancos_opcoes)
                    forma = st.selectbox("Forma Rec.", self.formas_opcoes)
                    
                    if st.form_submit_button("Salvar Receita"):
                        msg = self.fin.registrar_receita_manual(desc, val, cat_id, str(dt), banco, forma)
                        st.success(msg)
                        st.rerun()

        # --- Form Despesa ---
        with c2:
            with st.expander("➖ Nova Despesa", expanded=False):
                with st.form("form_des"):
                    desc = st.text_input("Descrição")
                    val = st.number_input("Valor (R$)", min_value=0.01)
                    
                    # Selectbox de Categorias (Despesa)
                    nome_cat = st.selectbox("Categoria", list(opcoes_despesa.keys()))
                    cat_id = opcoes_despesa[nome_cat]

                    dt = st.date_input("Data", value=date.today())
                    banco = st.selectbox("Conta Origem", self.bancos_opcoes)
                    forma = st.selectbox("Forma Pgto", self.formas_opcoes)
                    
                    if st.form_submit_button("Salvar Despesa"):
                        msg = self.fin.registrar_gasto_manual(desc, val, cat_id, str(dt), banco, forma)
                        st.success(msg)
                        st.rerun()

        st.divider()
        st.subheader("Extrato Detalhado")

        # Filtros
        fc1, fc2, fc3, fc4 = st.columns(4)
        d_ini = fc1.date_input("Início", value=date(date.today().year, 1, 1))
        d_fim = fc2.date_input("Fim", value=date.today())
        f_bancos = fc3.multiselect("Filtrar Bancos", self.bancos_opcoes)
        f_formas = fc4.multiselect("Filtrar Formas", self.formas_opcoes)

        dados = self.fin.gerar_extrato_detalhado(str(d_ini), str(d_fim), f_bancos, f_formas)

        if dados:
            df = pd.DataFrame(dados)
            def colorir_tipo(row):
                return ['background-color: #d4edda' if row['tipo'] == 'Receita' else 'background-color: #f8d7da'] * len(row)

            st.dataframe(
                df[['data', 'descricao', 'categoria', 'valor', 'banco', 'forma_pagamento', 'tipo']]
                .style.apply(colorir_tipo, axis=1),
                use_container_width=True,
                height=500
            )
            total = sum(d['valor'] for d in dados)
            st.caption(f"**Resultado do filtro:** R$ {total:.2f}")
        else:
            st.warning("Nada encontrado com estes filtros.")

    # ==========================================================================
    # 2. DASHBOARD
    # ==========================================================================
    def _render_dashboard(self):
        st.title("📊 Visão Geral")
        
        hoje = datetime.now()
        resumo = self.fin.get_resumo_mes(hoje.month, hoje.year)
        gastos = self.fin.get_gastos_por_categoria(hoje.month, hoje.year)

        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo Geral", f"R$ {resumo['saldo']:.2f}")
        c2.metric("Receitas (Mês)", f"R$ {resumo['receitas']:.2f}", delta="+")
        c3.metric("Despesas (Mês)", f"R$ {resumo['despesas']:.2f}", delta="-", delta_color="inverse")

        st.divider()

        col_graf, col_extrato = st.columns([1, 2])

        with col_graf:
            st.subheader("Gastos do Mês")
            if gastos and sum(gastos.values()) > 0:
                fig, ax = plt.subplots(figsize=(4, 4))
                ax.pie(gastos.values(), labels=gastos.keys(), autopct='%1.0f%%', startangle=90)
                fig.patch.set_alpha(0)
                st.pyplot(fig)
            else:
                st.info("Sem despesas registradas.")

        with col_extrato:
            st.subheader("Últimas Movimentações")
            extrato = self.fin.gerar_extrato_detalhado(f"{hoje.year}-01-01", f"{hoje.year}-12-31")
            
            if extrato:
                df = pd.DataFrame(extrato)
                df_show = df[['data', 'descricao', 'valor', 'banco', 'forma_pagamento']]
                df_show.columns = ['Data', 'Descrição', 'Valor', 'Banco', 'Forma']
                st.dataframe(df_show.head(8), hide_index=True, use_container_width=True)
            else:
                st.caption("Nenhuma movimentação.")

    # ==========================================================================
    # 3. KITNETS
    # ==========================================================================
    def _render_kitnets(self):
        st.title("🏠 Gestão de Kitnets")
        
        tab1, tab2, tab3 = st.tabs(["Lista Geral", "Novo Contrato/Imóvel", "💰 Receber Aluguel"])
        
        dados = self.kit.listar_kitnets_tabela()

        with tab1:
            if dados:
                df = pd.DataFrame(dados)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nenhuma kitnet cadastrada.")

        with tab2:
            st.subheader("Cadastro")
            tipo = st.radio("O que deseja cadastrar?", ["Nova Kitnet", "Novo Contrato"])
            
            if tipo == "Nova Kitnet":
                with st.form("fk"):
                    n = st.number_input("Número", min_value=1)
                    v = st.number_input("Valor Padrão", min_value=100.0)
                    if st.form_submit_button("Criar"):
                        st.success(self.kit.cadastrar_kitnet(n, v))
                        st.rerun()
            else:
                with st.form("fc"):
                    k_id = st.number_input("ID Kitnet", min_value=1)
                    i_id = st.number_input("ID Inquilino", min_value=1)
                    val = st.number_input("Valor Fechado", min_value=100.0)
                    dia = st.number_input("Dia Vencimento", 1, 31)
                    dt_ini = st.date_input("Início")
                    if st.form_submit_button("Gerar Contrato"):
                        st.success(self.kit.alugar_kitnet(k_id, i_id, val, int(dia), str(dt_ini)))
                        st.rerun()

        with tab3:
            st.write("Baixa Manual de Aluguel")
            c1, c2, c3 = st.columns(3)
            p_id = c1.number_input("ID do Pagamento (Boleto)", min_value=1)
            p_val = c2.number_input("Valor Recebido", min_value=0.0)
            p_banco = c3.selectbox("Recebido em:", self.bancos_opcoes)
            
            if st.button("Confirmar Recebimento", type="primary"):
                msg = self.kit.realizar_recebimento_aluguel(p_id, p_val, p_banco)
                st.success(msg)

    # ==========================================================================
    # 4. VEÍCULOS
    # ==========================================================================
    def _render_veiculos(self):
        st.title("🚚 Frota e Manutenção")
        
        frota = self.trans.listar_frota_simples()
        mapa_veiculos = {f"{v['modelo']} - {v['placa']}": v['id'] for v in frota} if frota else {}

        tab_lista, tab_gasto = st.tabs(["Minha Frota", "🛠️ Lançar Despesa"])

        with tab_lista:
            with st.expander("Cadastrar Novo Veículo"):
                with st.form("fv"):
                    m = st.text_input("Modelo")
                    p = st.text_input("Placa")
                    if st.form_submit_button("Salvar"):
                        st.success(self.trans.cadastrar_veiculo(m, p, 2024, "Uso"))
                        st.rerun()
            
            if frota:
                for v in frota:
                    icone = "✅" if v['status'] == 'ativo' else "🔧"
                    with st.container(border=True):
                        st.markdown(f"**{icone} {v['modelo']}** | {v['placa']}")
                        st.caption(f"Status: {v['status'].upper()} | Uso: {v['finalidade']}")

        with tab_gasto:
            if not frota:
                st.warning("Cadastre veículos primeiro.")
            else:
                st.info("Registre abastecimentos, mecânico, IPVA, etc.")
                with st.form("fg"):
                    nome_selecionado = st.selectbox("Veículo", list(mapa_veiculos.keys()))
                    id_v = mapa_veiculos[nome_selecionado]
                    
                    desc = st.text_input("Descrição (Ex: Gasolina Aditivada)")
                    val = st.number_input("Valor", min_value=0.01)
                    dt = st.date_input("Data")
                    
                    c1, c2 = st.columns(2)
                    banco = c1.selectbox("Pago via:", self.bancos_opcoes)
                    forma = c2.selectbox("Forma:", self.formas_opcoes)
                    
                    if st.form_submit_button("Lançar Gasto"):
                        msg = self.trans.lancar_gasto_direto(id_v, desc, val, str(dt), banco, forma)
                        st.success(msg)

    # ==========================================================================
    # 5. BOLETOS
    # ==========================================================================
    def _render_boletos(self):
        st.title("🧾 Contas a Pagar (Boletos)")
        
        totais = self.bol.calcular_totais()
        st.metric("Total Pendente", f"R$ {totais['total_geral']:.2f}")

        with st.expander("Novo Boleto"):
            with st.form("fb"):
                d = st.text_input("Descrição")
                v = st.number_input("Valor")
                dt = st.date_input("Vencimento")
                c = st.text_input("Código Barras")
                if st.form_submit_button("Agendar"):
                    self.bol.cadastrar_boleto(d, v, str(dt), 2, c)
                    st.success("Salvo!")
                    st.rerun()

        st.divider()
        boletos = self.bol.listar_boletos_detalhados()
        
        if boletos:
            for b in boletos:
                with st.container(border=True):
                    cols = st.columns([3, 1.5, 1])
                    with cols[0]:
                        st.markdown(f"**{b['descricao']}**")
                        st.caption(f"Vence: {b['vencimento_br']} | {b['status_texto']}")
                    with cols[1]:
                        banco_escolhido = st.selectbox("Pagar com:", self.bancos_opcoes, key=f"bk_{b['id']}")
                    with cols[2]:
                        st.write(f"**R$ {b['valor']:.2f}**")
                        if st.button("Pagar", key=f"btn_{b['id']}"):
                            msg = self.bol.pagar_boleto(b['id'], banco_escolhido)
                            st.success(msg)
                            st.rerun()
        else:
            st.success("Nenhuma conta pendente! 🎉")

    # ==========================================================================
    # 6. PIX
    # ==========================================================================
    def _render_pix(self):
        st.title("💠 Gerenciador Pix")
        
        with st.expander("Nova Chave"):
            with st.form("fpix"):
                t = st.text_input("Apelido")
                k = st.text_input("Chave")
                b = st.text_input("Banco")
                n = st.text_input("Titular")
                if st.form_submit_button("Salvar"):
                    self.pix.cadastrar_pix(t, k, "Auto", n, b)
                    st.rerun()

        lista = self.pix.listar_pix()
        for p in lista:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{p.titulo}** | {p.banco}\n\n`{p.chave}`")
                if c2.button("Excluir", key=f"del_{p.id_pix}"):
                    self.pix.excluir_pix(p.id_pix)
                    st.rerun()