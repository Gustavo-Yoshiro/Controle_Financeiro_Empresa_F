import streamlit as st
import pandas as pd
from datetime import date

from Service import RelatorioKitnetService 

class KitnetsPage:
    def __init__(self, inquilino_service, kitnet_service, locacao_service, 
                 relatorio_service: RelatorioKitnetService, 
                 financeiro_service, config_service):
        
        self.s_inquilino = inquilino_service
        self.s_kitnet = kitnet_service
        self.s_locacao = locacao_service
        self.s_relatorio = relatorio_service
        self.s_financeiro = financeiro_service
        self.cfg = config_service 

    def render(self):
        st.title("🏠 Gestão de Kitnets")
        
        # 1. Configurações
        bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
        formas_opcoes = self.cfg.listar_formas() or ["Dinheiro"]

        # 2. Garante atualização das cobranças antes de exibir
        self.s_locacao.gerar_cobrancas_mensais()

        # 3. Carrega Dados Visuais (Usando RelatorioService)
        dados_tabela = self.s_relatorio.montar_dashboard_kitnets()
        
        # Mapeamentos auxiliares para os SelectBoxes
        kits_livres = {k['numero']: k['id'] for k in dados_tabela if k['status'] == 'LIVRE'}
        todas_kits_map = {k['numero']: k['id'] for k in dados_tabela}

        # 4. Abas
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Lista Geral", 
            "📝 Novo Contrato", 
            "💰 Receber Aluguel", 
            "💸 Contas (IPTU/Água)",
            "👤 Inquilinos"
        ])

        # --- ABA 1: LISTAGEM GERAL ---
        with tab1:
            if dados_tabela:
               st.dataframe(pd.DataFrame(dados_tabela), width="stretch", hide_index=True)
            else:
                st.info("Nenhuma kitnet cadastrada.")

        # --- ABA 2: CADASTRO KITNET / CONTRATO ---
        with tab2:
            tipo = st.radio("O que deseja fazer?", ["Nova Kitnet", "Novo Contrato"], horizontal=True)
            st.write("") # Espaço

            if tipo == "Nova Kitnet":
                with st.form("fk"):
                    st.subheader("Cadastrar Imóvel")
                    c1, c2 = st.columns([1, 2])
                    ident = c1.selectbox("Bloco/Tipo", ["M1", "M2", "K", "Casa", "Apto"])
                    n = c2.number_input("Número", min_value=1, value=101)
                    v = st.number_input("Valor Padrão (R$)", min_value=100.0, value=800.0)
                    q = st.number_input("Quartos", min_value=1, value=1)
                    
                    if st.form_submit_button("Criar Kitnet"):
                        msg = self.s_kitnet.cadastrar(n, v, identificador=ident, quartos=q)
                        st.success(msg)
                        st.rerun()
            else:
                with st.form("fc"):
                    st.subheader("Novo Contrato de Aluguel")
                    
                    if not kits_livres:
                        st.warning("Não há kitnets livres.")
                        k_id_sel = None
                    else:
                        nome_k = st.selectbox("Selecione a Kitnet", list(kits_livres.keys()))
                        k_id_sel = kits_livres[nome_k]

                    # Chama InquilinoService para preencher o combo
                    inq_map = self.s_inquilino.listar_simples()
                    
                    if not inq_map:
                        st.warning("Cadastre inquilinos primeiro.")
                        i_id_sel = None
                    else:
                        nome_i = st.selectbox("Selecione o Inquilino", list(inq_map.keys()))
                        i_id_sel = inq_map[nome_i]

                    c1, c2, c3 = st.columns(3)
                    val = c1.number_input("Valor Fechado (R$)", value=800.0)
                    dia = c2.number_input("Dia Vencimento", 1, 31, value=5)
                    dt_ini = c3.date_input("Início Contrato", value=date.today())
                    
                    if st.form_submit_button("Gerar Contrato"):
                        if k_id_sel and i_id_sel:
                            msg = self.s_locacao.alugar(k_id_sel, i_id_sel, val, int(dia), str(dt_ini))
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Preencha todos os campos.")

        # --- ABA 3: RECEBIMENTO DE ALUGUEL ---
        with tab3:
            st.subheader("Contas a Receber (Pendentes)")
            
            # Chama RelatorioService para buscar a lista formatada
            pendencias_map = self.s_relatorio.listar_pendencias_formatadas()
            
            if not pendencias_map:
                st.success("Tudo em dia! Nenhum aluguel pendente. 🎉")
            else:
                with st.form("form_baixa_aluguel"):
                    selecao = st.selectbox("Selecione o Boleto:", list(pendencias_map.keys()))
                    id_pagamento_real = pendencias_map[selecao]
                    
                    c1, c2 = st.columns(2)
                    p_val = c1.number_input("Valor Recebido (R$)", min_value=0.0, step=10.0)
                    p_banco = c2.selectbox("Dinheiro entrou em:", bancos_opcoes)
                    
                    if st.form_submit_button("✅ Confirmar Recebimento"):
                        msg = self.s_locacao.processar_pagamento_aluguel(id_pagamento_real, p_val, p_banco)
                        st.success(msg)
                        st.rerun()

        # --- ABA 4: DESPESAS (IPTU/AGUA) ---
        with tab4:
            st.subheader("Lançar Despesa do Imóvel")
            
            with st.form("form_despesa_kit"):
                tipo_despesa = st.radio("Tipo:", ["Individual (Vinculada à Kitnet)", "Geral (Condomínio/Corredor)"], horizontal=True)
                id_sel = None
                nome_kit_ref = "Geral"
                
                if tipo_despesa.startswith("Individual"):
                    if todas_kits_map:
                        nome_k = st.selectbox("Qual Kitnet?", list(todas_kits_map.keys()))
                        id_sel = todas_kits_map[nome_k]
                        nome_kit_ref = nome_k
                    else:
                        st.warning("Cadastre kitnets primeiro.")
                
                desc = st.text_input("Descrição (Ex: IPTU, Manutenção Torneira)")
                
                c1, c2 = st.columns(2)
                val = c1.number_input("Valor (R$)", min_value=0.01)
                dt = c2.date_input("Data Pagamento", value=date.today())
                
                c3, c4 = st.columns(2)
                banco = c3.selectbox("Pago via:", bancos_opcoes, key="bk_k")
                forma = c4.selectbox("Forma:", formas_opcoes, key="fm_k")
                
                if st.form_submit_button("Lançar Conta"):
                    # Lógica de View: Monta a string bonita aqui
                    prefixo = f"[{nome_kit_ref}] " if id_sel else "[Condomínio] "
                    descricao_final = prefixo + desc
                    
                    msg = self.s_financeiro.registrar_despesa_imovel(
                        descricao=descricao_final, 
                        valor=val, 
                        id_kitnet=id_sel, 
                        data=str(dt), 
                        banco=banco, 
                        forma=forma
                    )
                    st.success(msg)

        # --- ABA 5: CADASTRO DE INQUILINOS ---
        with tab5:
            c_form, c_lista = st.columns([1, 1.5])
            
            with c_form:
                st.subheader("Novo Inquilino")
                with st.form("form_add_inq"):
                    nome = st.text_input("Nome Completo *")
                    cpf = st.text_input("CPF")
                    tel = st.text_input("Telefone")
                    email = st.text_input("Email")
                    prof = st.text_input("Profissão")
                    
                    c1, c2 = st.columns(2)
                    sexo = c1.selectbox("Sexo", ["M", "F", "Outro"])
                    est_civil = c2.selectbox("Est. Civil", ["Solteiro", "Casado", "Divorciado", "Viúvo"])
                    
                    obs = st.text_area("Obs")
                    
                    if st.form_submit_button("Cadastrar Pessoa"):
                        if nome:
                            msg = self.s_inquilino.cadastrar(nome, cpf, tel, sexo, est_civil, prof, email, obs)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning("Nome é obrigatório.")

            with c_lista:
                st.subheader("Pessoas Cadastradas")
                lista_inq = self.s_inquilino.admin_listar_todos()
                if lista_inq:
                    # Converte objetos para dict para exibir no dataframe
                    dados_inq = [{"ID": i.id_inquilino, "Nome": i.nome, "Tel": i.telefone, "CPF": i.cpf} for i in lista_inq]
                    st.dataframe(pd.DataFrame(dados_inq), width="stretch", hide_index=True)
                else:
                    st.info("Ninguém cadastrado.")