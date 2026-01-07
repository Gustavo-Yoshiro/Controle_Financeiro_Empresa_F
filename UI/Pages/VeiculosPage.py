import streamlit as st
from datetime import date

class VeiculosPage:
    def __init__(self, frota_service, empresa_service, logistica_service, relatorio_service, config_service):
        self.s_frota = frota_service       # Cuida do Carro (Cadastro/Manutenção)
        self.s_empresa = empresa_service   # Cuida do Cliente
        self.s_logistica = logistica_service # Cuida do Contrato e Pagamento
        self.s_relatorio = relatorio_service # Cuida da Leitura (KPIs e Listas)
        self.cfg = config_service          # Configurações gerais

    def render(self):
        st.title("🚚 Gestão de Frota")
        
        # 1. Carrega configs e roda robô de cobrança
        bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
        formas_opcoes = self.cfg.listar_formas() or ["Dinheiro"]
        self.s_logistica.gerar_cobrancas_mensais()

        # 2. KPIs do Topo (Dados Rápidos)
        # O RelatorioFrotaService calcula isso na hora
        kpis = self.s_relatorio.get_kpis_frota()
        faturamento = self.s_relatorio.get_faturamento_logistica()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Veículos", kpis['total_veiculos'])
        c2.metric("Disponíveis", kpis['disponiveis'])
        c3.metric("Taxa de Ocupação", f"{kpis['taxa_ocupacao']:.0f}%")
        c4.metric("Faturamento Total", f"R$ {faturamento:,.2f}")
        
        st.divider()

        # 3. Abas de Navegação
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Minha Frota", 
            "🏢 Empresas", 
            "📝 Novo Contrato", 
            "💰 Receber Alocação", 
            "🛠️ Manutenção"
        ])

        # --- ABA 1: FROTA ---
        with tab1:
            with st.expander("➕ Cadastrar Novo Veículo", expanded=False):
                with st.form("fv"):
                    c_a, c_b = st.columns(2)
                    m = c_a.text_input("Modelo (Ex: Fiat Uno)")
                    p = c_b.text_input("Placa")
                    
                    c_c, c_d = st.columns(2)
                    ano = c_c.number_input("Ano", min_value=1990, value=2024)
                    fin = c_d.text_input("Finalidade", value="Aluguel")

                    if st.form_submit_button("Salvar Veículo"):
                        if m and p:
                            msg = self.s_frota.cadastrar(m, p, ano, fin)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning("Preencha modelo e placa.")
            
            # Listagem Visual
            frota_completa = self.s_frota.admin_listar_todos() 
            
            if frota_completa:
                st.caption("Legenda: 🟢 Disponível | 🔴 Alocado | 🔧 Manutenção")
                for v in frota_completa:
                    icone = "🟢" if v.status == 'ativo' else "🔴" if v.status == 'alocado' else "🔧"
                    cor_borda = True if v.status == 'alocado' else False
                    
                    with st.container(border=True):
                        col_i, col_d = st.columns([0.5, 4])
                        col_i.title(icone)
                        col_d.markdown(f"### {v.modelo} ({v.ano})")
                        col_d.markdown(f"**Placa:** `{v.placa}` | **Status:** {v.status.upper()}")
            else:
                st.info("Nenhum veículo cadastrado.")

        # --- ABA 2: EMPRESAS ---
        with tab2:
            c_form, c_list = st.columns([1, 2])
            with c_form:
                st.subheader("Nova Empresa")
                with st.form("f_emp"):
                    raz = st.text_input("Razão Social")
                    cnpj = st.text_input("CNPJ")
                    tel = st.text_input("Telefone")
                    if st.form_submit_button("Cadastrar"):
                        self.s_empresa.cadastrar(raz, cnpj, tel)
                        st.success("Salvo!")
                        st.rerun()
            
            with c_list:
                st.subheader("Clientes Cadastrados")
                lista_emp = self.s_empresa.admin_listar_todas()
                if lista_emp:
                    for e in lista_emp:
                        st.text(f"🏢 {e.razao_social} (CNPJ: {e.cnpj})")
                else:
                    st.info("Nenhuma empresa cadastrada.")

        # --- ABA 3: CONTRATO ---
        with tab3:
            st.subheader("Alocar Veículo")
            
            # Mapas para Selectbox
            empresas_map = self.s_empresa.listar_para_select() 
            
            # Busca apenas veículos ativos
            frota_completa = self.s_frota.admin_listar_todos()
            veiculos_map = {f"{v.modelo} - {v.placa}": v.id_veiculo for v in frota_completa if v.status == 'ativo'}

            with st.form("f_con_alo"):
                if not empresas_map:
                    st.warning("Cadastre Empresas na aba anterior.")
                elif not veiculos_map:
                    st.warning("Sem veículos disponíveis (ativos).")
                else:
                    emp_nome = st.selectbox("Cliente", list(empresas_map.keys()))
                    veic_nome = st.selectbox("Veículo Disponível", list(veiculos_map.keys()))
                    
                    c1, c2, c3 = st.columns(3)
                    val = c1.number_input("Valor Mensal (R$)", min_value=100.0, value=1500.0)
                    dia = c2.number_input("Dia Vencimento", 1, 31, value=10)
                    dt_ini = c3.date_input("Início Contrato", value=date.today())
                    
                    if st.form_submit_button("Firmar Contrato"):
                        # Chama LogisticaService
                        msg = self.s_logistica.criar_contrato(
                            empresas_map[emp_nome], 
                            veiculos_map[veic_nome], 
                            val, 
                            int(dia),
                            str(dt_ini)
                        )
                        st.success(msg)
                        st.balloons()
                        st.rerun()

        # --- ABA 4: RECEBER ---
        with tab4:
            st.subheader("Faturas de Alocação Pendentes")
            
            pendencias = self.s_relatorio.listar_pendencias_formatadas()
            
            if not pendencias:
                st.success("Tudo recebido! Nenhuma alocação pendente. 🎉")
            else:
                with st.form("rec_alo"):
                    sel = st.selectbox("Selecione a Fatura:", list(pendencias.keys()))
                    id_pag = pendencias[sel]
                    
                    c1, c2 = st.columns(2)
                    val_recebido = c1.number_input("Valor Recebido (R$)", min_value=0.0)
                    banco_rec = c2.selectbox("Entrou em:", bancos_opcoes)
                    
                    if st.form_submit_button("Confirmar Recebimento"):
                        msg = self.s_logistica.processar_recebimento(id_pag, val_recebido, banco_rec)
                        st.success(msg)
                        st.rerun()

        # --- ABA 5: DESPESAS ---
        with tab5:
            st.subheader("Lançar Manutenção/Gasto")
            
            # Lista todos os veículos (mesmo alocados geram despesa para o dono)
            frota_dicts = self.s_relatorio.listar_frota_simples()
            
            if not frota_dicts:
                st.warning("Sem veículos.")
            else:
                # O Relatorio retorna dict com 'label' ou montamos aqui
                all_veic_map = {}
                for v in frota_dicts:
                    # Tenta pegar 'label', senao monta
                    lbl = v.get('label', f"{v.get('modelo')} - {v.get('placa')}")
                    all_veic_map[lbl] = v['id']

                with st.form("fg"):
                    v_nome = st.selectbox("Veículo", list(all_veic_map.keys()))
                    id_v = all_veic_map[v_nome]
                    
                    desc = st.text_input("Descrição (Ex: Troca de Óleo, Pneu)")
                    
                    c1, c2 = st.columns(2)
                    val = c1.number_input("Valor (R$)", min_value=0.01)
                    dt = c2.date_input("Data Pagamento", value=date.today())
                    
                    c3, c4 = st.columns(2)
                    banco = c3.selectbox("Pago via:", bancos_opcoes)
                    forma = c4.selectbox("Forma:", formas_opcoes)
                    
                    if st.form_submit_button("Lançar Gasto"):
                        msg = self.s_frota.lancar_manutencao(id_v, desc, val, str(dt), banco, forma)
                        st.success(msg)