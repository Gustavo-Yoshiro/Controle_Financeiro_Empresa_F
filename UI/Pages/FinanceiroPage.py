import streamlit as st
import pandas as pd
from datetime import date

class FinanceiroPage:
    def __init__(self, financeiro_service, categoria_service, relatorio_service, config_service):
        self.s_financeiro = financeiro_service  # Facade para escrita
        self.s_categoria = categoria_service    # Leitura de categorias
        self.s_relatorio = relatorio_service    # Leitura de extratos
        self.cfg = config_service               # Configurações (Bancos/Formas)

    def render(self):
        st.title("📝 Transações Avulsas")
        
        # =====================================================================
        # 1. CARREGAR DADOS AUXILIARES
        # =====================================================================
        
        bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
        formas_opcoes = self.cfg.listar_formas() or ["Dinheiro"]
        
        # Busca categorias e separa por tipo para facilitar a vida do usuário
        todas_cats = self.s_categoria.listar_todas()
        
        opcoes_receita = {c['nome']: c['id'] for c in todas_cats if c['tipo'] == 'receita'}
        opcoes_despesa = {c['nome']: c['id'] for c in todas_cats if c['tipo'] == 'despesa'}

        # Fallbacks de segurança caso não tenha categorias cadastradas
        if not opcoes_receita: opcoes_receita = {"Geral (R)": 1}
        if not opcoes_despesa: opcoes_despesa = {"Geral (D)": 2}

        # =====================================================================
        # 2. ÁREA DE FILTROS (EXTRATO)
        # =====================================================================
        
        with st.expander("🔍 Filtros do Extrato", expanded=False):
            fc1, fc2, fc3, fc4 = st.columns(4)
            # Define padrão: Dia 1 do ano até hoje
            d_ini = fc1.date_input("Início", value=date(date.today().year, 1, 1))
            d_fim = fc2.date_input("Fim", value=date.today())
            f_bancos = fc3.multiselect("Filtrar Bancos", bancos_opcoes)
            f_formas = fc4.multiselect("Filtrar Formas", formas_opcoes)

        st.divider()

        # =====================================================================
        # 3. FORMULÁRIOS DE LANÇAMENTO (EXPANSÍVEIS)
        # =====================================================================

        c1, c2 = st.columns(2)
        
        # --- Form Receita ---
        with c1:
            with st.expander("➕ Nova Receita", expanded=False):
                with st.form("form_rec"):
                    desc = st.text_input("Descrição (Ex: Freelance, Venda)")
                    val = st.number_input("Valor (R$)", min_value=0.01)
                    
                    nome_cat = st.selectbox("Categoria", list(opcoes_receita.keys()))
                    cat_id = opcoes_receita[nome_cat]
                    
                    dt = st.date_input("Data", value=date.today())
                    
                    c_b, c_f = st.columns(2)
                    banco = c_b.selectbox("Destino", bancos_opcoes, key="bk_rec")
                    forma = c_f.selectbox("Forma", formas_opcoes, key="fm_rec")
                    
                    # Nota: Nos botões, mantemos use_container_width=True pois geralmente
                    # a mudança para 'stretch' afeta principalmente st.dataframe/st.data_editor.
                    # Se der erro aqui também, mude para width='stretch'.
                    if st.form_submit_button("Salvar Receita", use_container_width=True):
                        if not desc:
                            st.warning("Digite uma descrição.")
                        else:
                            msg = self.s_financeiro.registrar_receita_manual(
                                descricao=desc, 
                                valor=val, 
                                id_categoria=cat_id, 
                                data=str(dt), 
                                banco=banco, 
                                forma=forma
                            )
                            st.success(msg)
                            st.rerun()

        # --- Form Despesa ---
        with c2:
            with st.expander("➖ Nova Despesa", expanded=False):
                with st.form("form_des"):
                    desc = st.text_input("Descrição (Ex: Almoço, Uber)")
                    val = st.number_input("Valor (R$)", min_value=0.01)
                    
                    nome_cat = st.selectbox("Categoria", list(opcoes_despesa.keys()))
                    cat_id = opcoes_despesa[nome_cat]
                    
                    dt = st.date_input("Data", value=date.today())
                    
                    c_b, c_f = st.columns(2)
                    banco = c_b.selectbox("Origem", bancos_opcoes, key="bk_des")
                    forma = c_f.selectbox("Forma", formas_opcoes, key="fm_des")
                    
                    if st.form_submit_button("Salvar Despesa", use_container_width=True):
                        if not desc:
                            st.warning("Digite uma descrição.")
                        else:
                            msg = self.s_financeiro.registrar_gasto_manual(
                                descricao=desc, 
                                valor=val, 
                                id_categoria=cat_id, 
                                data_gasto=str(dt), 
                                banco=banco, 
                                forma=forma
                            )
                            st.success(msg)
                            st.rerun()

        # =====================================================================
        # 4. EXTRATO DETALHADO
        # =====================================================================
        st.subheader("Extrato do Período")

        dados = self.s_relatorio.gerar_extrato(
            str(d_ini), str(d_fim), f_bancos, f_formas
        )

        if dados:
            df = pd.DataFrame(dados)
            
            def colorir_tipo(row):
                if row['tipo'] == 'Receita':
                    return ['background-color: rgba(144, 238, 144, 0.2)'] * len(row)
                else:
                    return ['background-color: rgba(255, 99, 71, 0.1)'] * len(row)

            # --- CORREÇÃO AQUI ---
            # Substituído use_container_width=True por width="stretch"
            st.dataframe(
                df[['data', 'descricao', 'categoria', 'valor', 'banco', 'forma', 'tipo']]
                .style.apply(colorir_tipo, axis=1)
                .format({"valor": "R$ {:.2f}"}), 
                width="stretch",  # <--- Nova sintaxe
                height=500,
                hide_index=True
            )
            
            total = sum(d['valor'] for d in dados)
            entradas = sum(d['valor'] for d in dados if d['valor'] > 0)
            saidas = sum(d['valor'] for d in dados if d['valor'] < 0)
            
            ct1, ct2, ct3 = st.columns(3)
            ct1.metric("Entradas", f"R$ {entradas:,.2f}")
            ct2.metric("Saídas", f"R$ {saidas:,.2f}")
            ct3.metric("Saldo Líquido", f"R$ {total:,.2f}", delta_color="normal")
            
        else:
            st.info("Nenhuma transação encontrada com estes filtros.")