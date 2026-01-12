import streamlit as st
import pandas as pd
from datetime import date

class VeiculosPage:
    def __init__(self, frota_service, empresa_service, logistica_service, relatorio_service, config_service):
        self.s_frota = frota_service       # Cadastro/Manutenção de Veículos
        self.s_empresa = empresa_service   # Cadastro de Empresas
        self.s_logistica = logistica_service # Lógica de Contrato e Pagamento
        self.s_relatorio = relatorio_service # Relatórios Inteligentes
        self.cfg = config_service          # Configurações gerais

    def render(self):
        st.title("🚚 Gestão de Frota")
        
        # 1. Configurações e Robô Mensal
        bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
        formas_opcoes = self.cfg.listar_formas() or ["Dinheiro"]
        
        # Garante que as faturas do mês atual existam
        self.s_logistica.gerar_cobrancas_mensais()

        # 2. KPIs do Topo
        kpis = self.s_relatorio.get_kpis_frota()
        faturamento = self.s_relatorio.get_faturamento_logistica()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Veículos", kpis['total_veiculos'])
        c2.metric("Disponíveis", kpis['disponiveis'])
        c3.metric("Taxa de Ocupação", f"{kpis['taxa_ocupacao']:.0f}%")
        c4.metric("Faturamento Acumulado", f"R$ {faturamento:,.2f}")
        
        st.divider()

        # 3. Abas de Navegação
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Minha Frota (Painel)", 
            "🏢 Empresas", 
            "📝 Novo Contrato", 
            "💰 Receber Alocação", 
            "🛠️ Manutenção"
        ])

        # --- ABA 1: PAINEL INTELIGENTE (IGUAL KITNETS) ---
        with tab1:
            with st.expander("🔎 Filtros de Período", expanded=True):
                c_ano, c_mes = st.columns([1, 1])
                
                # Filtro Ano
                ano_atual = date.today().year
                lista_anos = list(range(ano_atual - 2, ano_atual + 4))
                sel_ano = c_ano.selectbox("Ano", lista_anos, index=lista_anos.index(ano_atual))

                # Filtro Mês
                mes_atual = date.today().month
                mapa_meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
                lista_meses_str = [f"{k:02d} - {v}" for k, v in mapa_meses.items()]
                sel_mes_str = c_mes.selectbox("Mês", lista_meses_str, index=mes_atual - 1)

                mes_num = sel_mes_str.split(" - ")[0]
                mes_ref_str = f"{sel_ano}-{mes_num}"

            # Cadastrar Novo Veículo (Botão Rápido)
            with st.popover("➕ Cadastrar Veículo"):
                with st.form("fv"):
                    m = st.text_input("Modelo (Ex: Fiat Uno)")
                    p = st.text_input("Placa")
                    ano = st.number_input("Ano", min_value=1990, value=2024)
                    fin = st.text_input("Finalidade", value="Aluguel")
                    if st.form_submit_button("Salvar"):
                        if m and p:
                            msg = self.s_frota.cadastrar(m, p, ano, fin)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning("Preencha modelo e placa.")

            # GERA O RELATÓRIO
            dados = self.s_relatorio.gerar_painel_frota(mes_ref=mes_ref_str)
            df = pd.DataFrame(dados)

            if not df.empty:
                st.markdown(f"### Status em **{mapa_meses[int(mes_num)]}/{sel_ano}**")
                
                def colorir(val):
                    color = ''
                    if isinstance(val, str):
                        if '⚠️' in val: return 'color: red; font-weight: bold'
                        if 'ATRASADO' in val: return 'color: red'
                        if 'PAGO' in val: return 'color: green'
                        if 'PARCIAL' in val: return 'color: orange'
                        if 'A VENCER' in val: return 'color: blue'
                    return color

                st.dataframe(
                    df.style.map(colorir, subset=['Situação Mês', 'Alertas']), 
                    width='stretch', 
                    hide_index=True,
                    height=500
                )
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
                        if raz:
                            self.s_empresa.cadastrar(raz, cnpj, tel)
                            st.success("Salvo!")
                            st.rerun()
                        else:
                            st.warning("Nome obrigatório.")
            
            with c_list:
                st.subheader("Clientes Cadastrados")
                lista_emp = self.s_empresa.admin_listar_todas()
                if lista_emp:
                    # Converte para DataFrame para ficar bonito
                    df_emp = pd.DataFrame([{"Empresa": e.razao_social, "CNPJ": e.cnpj, "Tel": e.telefone} for e in lista_emp])
                    st.dataframe(df_emp, width='stretch', hide_index=True)
                else:
                    st.info("Nenhuma empresa cadastrada.")

        # --- ABA 3: CONTRATO ---
        with tab3:
            st.subheader("Alocar Veículo")
            
            # Mapas para Selectbox
            empresas_map = self.s_empresa.listar_para_select() 
            
            # Busca apenas veículos ativos (disponíveis)
            frota_completa = self.s_frota.admin_listar_todos()
            veiculos_map = {f"{v.modelo} - {v.placa}": v.id_veiculo for v in frota_completa if v.status == 'ativo'}

            with st.form("f_con_alo"):
                if not empresas_map:
                    st.warning("Cadastre Empresas na aba anterior.")
                    emp_sel = None
                elif not veiculos_map:
                    st.warning("Sem veículos disponíveis (todos alocados ou em manutenção).")
                    veic_sel = None
                else:
                    emp_nome = st.selectbox("Cliente", list(empresas_map.keys()))
                    veic_nome = st.selectbox("Veículo Disponível", list(veiculos_map.keys()))
                    emp_sel = empresas_map[emp_nome]
                    veic_sel = veiculos_map[veic_nome]
                    
                    c1, c2, c3 = st.columns(3)
                    val = c1.number_input("Valor Mensal (R$)", min_value=100.0, value=1500.0)
                    dia = c2.number_input("Dia Vencimento", 1, 31, value=10)
                    dt_ini = c3.date_input("Início Contrato", value=date.today())
                    
                    if st.form_submit_button("Firmar Contrato"):
                        if emp_sel and veic_sel:
                            msg = self.s_logistica.criar_contrato(
                                emp_sel, veic_sel, val, int(dia), str(dt_ini)
                            )
                            st.success(msg)
                            st.balloons()
                            st.rerun()

        # --- ABA 4: RECEBER (COM LÓGICA DINÂMICA) ---
        with tab4:
            st.subheader("Faturas de Alocação Pendentes")
            
            # 1. Pega a lista de pendências do Service (já calculada)
            # Retorna lista de dicts: [{'label_combo': '...', 'id_pagamento': 1, 'valor_restante': 500}, ...]
            lista_pendencias = self.s_logistica.listar_faturas_pendentes()
            
            if not lista_pendencias:
                st.success("Tudo recebido! Nenhuma alocação pendente. 🎉")
            else:
                # Cria mapa para o selectbox
                mapa_faturas = {item['label_combo']: item for item in lista_pendencias}
                
                # Selectbox fora do form para atualizar a tela
                sel_fatura = st.selectbox("Selecione a Fatura:", list(mapa_faturas.keys()))
                
                # Pega os dados da seleção
                dados_fatura = mapa_faturas[sel_fatura]
                val_sugerido = float(dados_fatura['valor_restante'])
                
                st.divider()
                
                c1, c2 = st.columns(2)
                # Input já vem preenchido com o que falta
                val_recebido = c1.number_input("Valor a Receber Agora (R$)", min_value=0.0, value=val_sugerido)
                banco_rec = c2.selectbox("Entrou em:", bancos_opcoes)
                obs = st.text_input("Observação (Opcional)")
                
                if val_recebido < (val_sugerido - 0.05):
                    st.info(f"💡 Pagamento Parcial: Ficará faltando R$ {val_sugerido - val_recebido:.2f}")
                
                if st.button("Confirmar Recebimento", type="primary"):
                    msg = self.s_logistica.processar_recebimento(
                        dados_fatura['id_pagamento'], val_recebido, banco_rec, obs
                    )
                    st.success(msg)
                    st.rerun()

        # --- ABA 5: DESPESAS ---
        with tab5:
            st.subheader("Lançar Manutenção/Gasto")
            
            # Lista todos os veículos (Select Simples)
            frota_dicts = self.s_relatorio.listar_frota_simples()
            
            if not frota_dicts:
                st.warning("Sem veículos.")
            else:
                # Monta dict {Label: ID}
                all_veic_map = {f"{v['modelo']} - {v['placa']}": v['id'] for v in frota_dicts}

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