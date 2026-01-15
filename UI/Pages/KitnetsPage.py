import streamlit as st
import pandas as pd
from datetime import date, datetime
from Utils.Validadores import validar_cpf, validar_telefone, validar_email

class KitnetsPage:
    def __init__(self, inquilino_service, kitnet_service, locacao_service, 
                relatorio_service, financeiro_service, config_service):
        
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

        # 2. Garante atualização das cobranças
        self.s_locacao.gerar_cobrancas_mensais()

        # 3. Carrega Dados Básicos
        todas_kitnets_obj = self.s_kitnet.admin_listar_todas()
        
        # Mapeamentos auxiliares
        kits_livres = {f"{k.identificador}-{k.numero}": k.id_kitnet for k in todas_kitnets_obj if k.status == 'LIVRE'}
        todas_kits_map = {f"{k.identificador}-{k.numero}": k.id_kitnet for k in todas_kitnets_obj}
        lista_apenas_blocos = sorted(list(set([k.identificador for k in todas_kitnets_obj])))

        # 4. Abas
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Lista Geral", 
            "Novo Contrato", 
            "💰 Receber Aluguel", 
            "💸 Contas & Taxas",
            "👤 Inquilinos",
            "🚪 Desocupação / Encerrar"
        ])

        # --- ABA 1: LISTAGEM GERAL ---
        with tab1:
            with st.expander("🔎 Filtros Avançados", expanded=True):
                c_ano, c_mes, c_status, c_inq, c_kit = st.columns([1, 1.5, 2, 2, 1.5])
                
                # --- Filtros ---
                ano_atual = date.today().year
                lista_anos = list(range(ano_atual - 2, ano_atual + 4))
                sel_ano = c_ano.selectbox("Ano", lista_anos, index=lista_anos.index(ano_atual))

                mes_atual = date.today().month
                mapa_meses = {
                    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
                    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
                }
                lista_meses_str = [f"{k:02d} - {v}" for k, v in mapa_meses.items()]
                sel_mes_str = c_mes.selectbox("Mês", lista_meses_str, index=mes_atual - 1)

                mes_num = sel_mes_str.split(" - ")[0] 
                mes_ref_str = f"{sel_ano}-{mes_num}"

                filtro_status = c_status.selectbox(
                    "Situação Financeira", 
                    ["Todos", "✅ Pagos", "🔴 Pendentes/Atrasados", "⚠️ Com Dívida Antiga", "⚪ Livres"]
                )

                # --- CARREGAMENTO ---
                dados_tabela = self.s_relatorio.gerar_painel_geral(mes_ref=mes_ref_str)
                df = pd.DataFrame(dados_tabela)

                # --- LÓGICA DE CORREÇÃO: Pega Valor e Data do Contrato Real ---
                if not df.empty and "Identificação" in df.columns:
                    # Busca todos os contratos ativos para cruzar dados
                    contratos_ativos = self.s_locacao.listar_ativas()
                    # Cria um mapa rápido: "M1-101" -> Dados do Contrato
                    map_contratos = {f"{c['identificador']}-{c['numero']}": c for c in contratos_ativos}

                    vals_reais = []
                    inicios_reais = []
                    
                    for idx, row in df.iterrows():
                        ident = row["Identificação"]
                        if ident in map_contratos:
                            # Se tem contrato ativo, usa os dados do contrato
                            c_dados = map_contratos[ident]
                            vals_reais.append(f"R$ {c_dados['valor']:.2f}")
                            
                            # Formata a data de início (YYYY-MM-DD -> DD/MM/YYYY)
                            try:
                                dt_fmt = datetime.strptime(c_dados['data_inicio'], "%Y-%m-%d").strftime("%d/%m/%Y")
                            except:
                                dt_fmt = c_dados['data_inicio']
                            inicios_reais.append(dt_fmt)
                        else:
                            # Se não tem contrato (Livre), mantém o que veio ou traço
                            val_orig = row.get("Valor", 0)
                            try:
                                vals_reais.append(f"R$ {float(val_orig):.2f}" if val_orig else "-")
                            except:
                                vals_reais.append(f"R$ {val_orig}" if val_orig else "-")
                            inicios_reais.append("-")

                    # Atualiza/Cria as colunas no DataFrame
                    df["Valor (Contrato)"] = vals_reais
                    df["Início Contrato"] = inicios_reais
                    
                    # Opcional: Remover a coluna "Valor" antiga se quiser limpar a visão
                    if "Valor" in df.columns:
                        df = df.drop(columns=["Valor"])

                lista_inq = ["Todos"] + list(df[df["Inquilino"] != "---"]["Inquilino"].unique()) if not df.empty else ["Todos"]
                filtro_inq = c_inq.selectbox("Inquilino", lista_inq)

                lista_kits = ["Todas"] + list(df["Identificação"].unique()) if not df.empty else ["Todas"]
                filtro_kit = c_kit.selectbox("Kitnet", lista_kits)

            # --- APLICAÇÃO DOS FILTROS ---
            if not df.empty:
                if filtro_inq != "Todos":
                    df = df[df["Inquilino"] == filtro_inq]
                
                if filtro_kit != "Todas":
                    df = df[df["Identificação"] == filtro_kit]

                if filtro_status == "✅ Pagos":
                    df = df[df["Situação Mês"].str.contains("PAGO")]
                elif filtro_status == "🔴 Pendentes/Atrasados":
                    df = df[
                        df["Situação Mês"].str.contains("ATRASADO") | 
                        df["Situação Mês"].str.contains("PARCIAL") | 
                        df["Situação Mês"].str.contains("A VENCER") |
                        df["Situação Mês"].str.contains("Aguardando")
                    ]
                elif filtro_status == "⚠️ Com Dívida Antiga":
                    df = df[df["Alertas"].str.contains("⚠️")]
                elif filtro_status == "⚪ Livres":
                    df = df[df["Status Imóvel"] == "LIVRE"]

                st.markdown(f"#### Resultados de **{mapa_meses[int(mes_num)]}/{sel_ano}**: {len(df)} imóveis")
                
                def colorir_situacao(val):
                    color = ''
                    if isinstance(val, str):
                        if '⚠️' in val: color = 'color: red; font-weight: bold'
                        elif 'ATRASADO' in val: color = 'color: red'
                        elif 'PAGO' in val: color = 'color: green'
                        elif 'PARCIAL' in val: color = 'color: orange'
                        elif 'A VENCER' in val: color = 'color: blue'
                    return color

                st.dataframe(
                    df.style.map(colorir_situacao, subset=['Situação Mês', 'Alertas']), 
                    width='stretch', # <--- CORREÇÃO: Substitui width=2000
                    hide_index=True
                )
            else:
                st.info(f"Nenhum registro encontrado para {mes_ref_str}.")

        # --- ABA 2: CADASTRO KITNET / CONTRATO ---
        with tab2:
            tipo = st.radio("O que deseja fazer?", ["Nova Kitnet", "Novo Contrato"], horizontal=True)
            
            if tipo == "Nova Kitnet":
                with st.expander("Cadastrar Imóvel", expanded=True):
                    # Adicionado clear_on_submit=True para limpar após cadastrar
                    with st.form("fk", clear_on_submit=True):
                        c1, c2 = st.columns([1, 2])
                        ident = c1.selectbox("Bloco/Tipo", ["M1", "M2", "Casa", "Apto"])
                        n = c2.number_input("Número", min_value=1, value=101)
                        v = st.number_input("Valor Padrão (R$)", min_value=100.0, value=800.0)
                        
                        if st.form_submit_button("Criar Kitnet"):
                            msg = self.s_kitnet.cadastrar(n, v, identificador=ident)
                            st.success(msg)
            else:
                with st.expander("Novo Contrato de Aluguel", expanded=True):
                    # Adicionado clear_on_submit=True para limpar após cadastrar
                    with st.form("fc", clear_on_submit=True):
                        if not kits_livres:
                            st.warning("Não há kitnets livres no momento.")
                            k_id_sel = None
                        else:
                            nome_k = st.selectbox("Selecione a Kitnet", list(kits_livres.keys()))
                            k_id_sel = kits_livres[nome_k]

                        inq_map = self.s_inquilino.listar_simples()
                        
                        if not inq_map:
                            st.warning("Cadastre inquilinos na aba 'Inquilinos' primeiro.")
                            i_id_sel = None
                        else:
                            nome_i = st.selectbox("Selecione o Inquilino", list(inq_map.keys()))
                            i_id_sel = inq_map[nome_i]

                        st.markdown("---")
                        st.markdown("###### 💲 Financeiro")
                        c1, c2, c3 = st.columns(3)
                        val_aluguel = c1.number_input("Valor Aluguel (R$)", value=800.0)
                        val_esgoto = c2.number_input("Taxa Fixa Mensal (Se houver) (R$)", value=0.0, help="Deixe 0.00 se for cobrar variável na Aba 'Contas'")
                        dia = c3.number_input("Dia Vencimento", 1, 31, value=10)
                        
                        st.markdown("###### 🛋️ Detalhes e Arquivos")
                        c4, c5 = st.columns([1, 2])
                        dt_ini = c4.date_input("Início Contrato", value=date.today())
                        
                        eh_mobiliado = c4.checkbox("Possui Mobília?", value=False)
                        arquivo_contrato = c5.file_uploader("Anexar Contrato Assinado", type=["pdf", "docx", "doc", "jpg", "png"])
                        
                        obs_mob = st.text_area("Descrição da Mobília (Opcional)", 
                                             placeholder="Ex: Cama box, Geladeira Electrolux, Fogão 4 bocas...")
                        
                        if st.form_submit_button("Gerar Contrato"):
                            if k_id_sel and i_id_sel:
                                mob_int = 1 if eh_mobiliado else 0
                                
                                msg = self.s_locacao.alugar(
                                    id_kitnet=k_id_sel, 
                                    id_inquilino=i_id_sel, 
                                    valor_aluguel=val_aluguel,
                                    valor_esgoto=val_esgoto,
                                    dia_vencimento=int(dia), 
                                    data_inicio=str(dt_ini),
                                    mobiliado=mob_int,
                                    obs_mobiliado=obs_mob,
                                    arquivo_upload=arquivo_contrato
                                )
                                # Verifica sucesso ou falha na mensagem retornada
                                if "Erro" in msg:
                                    st.error(msg)
                                else:
                                    st.success(msg)
                            else:
                                st.error("Preencha todos os campos obrigatórios.")

        # --- ABA 3: RECEBIMENTO DE ALUGUEL ---
        with tab3:
            st.subheader("Contas a Receber (Pendentes)")
            
            lista_pendentes = self.s_locacao.listar_alugueis_pendentes()
            
            if not lista_pendentes:
                st.success("Tudo em dia! Nenhum aluguel pendente ou parcial. 🎉")
            else:
                map_pendencias = {item['label_combo']: item for item in lista_pendentes}
                
                sel_txt = st.selectbox("Selecione a cobrança:", list(map_pendencias.keys()))
                dados_cobranca = map_pendencias[sel_txt]
                
                st.markdown("---")
                col_res1, col_res2, col_res3 = st.columns(3)
                col_res1.metric("Valor Total Esperado", f"R$ {dados_cobranca['valor_total_esperado']:.2f}")
                col_res2.metric("Já Pago", f"R$ {dados_cobranca['valor_ja_pago']:.2f}")
                col_res3.metric("Restante a Pagar", f"R$ {dados_cobranca['valor_restante']:.2f}", delta_color="inverse")
                st.markdown("---")
                
                st.write("#### Detalhes do Pagamento")
                
                c1, c2 = st.columns(2)
                val_sugerido = float(dados_cobranca['valor_restante'])
                
                valor_recebido = c1.number_input("Valor Recebido Agora (R$)", min_value=0.0, step=10.0, value=val_sugerido)
                banco_rec = c2.selectbox("Dinheiro entrou em:", bancos_opcoes)
                
                obs = st.text_input("Observação (Opcional)")

                eh_acordo = False
                if valor_recebido < (val_sugerido - 0.05):
                    st.warning(f"⚠️ Atenção: Falta R$ {val_sugerido - valor_recebido:.2f} para quitar.")
                    tipo_baixa = st.radio(
                        "Como deseja processar essa diferença?",
                        [
                            "🟢 Pagamento Parcial (Inquilino paga o resto depois)",
                            "🔴 Desconto/Acordo (Perdoar o resto e quitar o mês)"
                        ]
                    )
                    if "Desconto" in tipo_baixa:
                        eh_acordo = True
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("Confirmar Recebimento", type="primary", width='stretch'):
                    msg = self.s_locacao.processar_pagamento_aluguel(
                        id_pagamento=dados_cobranca['id_pagamento'], 
                        valor_recebido=valor_recebido, 
                        banco=banco_rec,
                        eh_quitacao_com_desconto=eh_acordo,
                        obs=obs
                    )
                    if "Sucesso" in msg:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # --- ABA 4: DESPESAS E TAXAS VARIÁVEIS ---
        with tab4:
            st.title("💸 Despesas e Taxas Extras")
            
            aba_taxas, aba_despesas = st.tabs(["💧 Lançar Esgoto/Água (Cobrança)", "🧾 Registrar Despesa (Saída)"])

            # --- SUB-ABA 1: LANÇAR TAXA NO ALUGUEL ---
            with aba_taxas:
                st.info("Use esta área para adicionar o valor da água/esgoto na conta de todos os inquilinos ativos de um Bloco.")
                
                if not lista_apenas_blocos:
                    st.warning("Cadastre kitnets para ter Blocos disponíveis.")
                else:
                    with st.form("form_lanca_taxa"):
                        col_a, col_b = st.columns(2)
                        bloco_alvo = col_a.selectbox("Selecione o Bloco", lista_apenas_blocos)
                        
                        # Seletor de Mês (igual ao filtro lá de cima, mas simplificado)
                        mes_taxa = date.today().month
                        ano_taxa = date.today().year
                        mes_ref_taxa = f"{ano_taxa}-{mes_taxa:02d}"
                        
                        col_b.text_input("Mês Referência (Cobrança)", value=mes_ref_taxa, disabled=True, help="O valor será somado ao boleto deste mês.")
                        
                        col_c, col_d = st.columns(2)
                        nome_taxa = col_c.text_input("Nome da Taxa", value="Esgoto Variável")
                        valor_por_unidade = col_d.number_input("Valor por Inquilino (R$)", min_value=0.01, step=0.50)

                        if st.form_submit_button("💰 Adicionar Taxa a Todos do Bloco"):
                            msg = self.s_locacao.lancar_cobranca_variavel_em_lote(
                                bloco_alvo=bloco_alvo,
                                valor_por_inquilino=valor_por_unidade,
                                mes_ref=mes_ref_taxa,
                                nome_taxa=nome_taxa
                            )
                            if "Sucesso" in msg:
                                st.success(msg)
                            else:
                                st.warning(msg)

            # --- SUB-ABA 2: REGISTRAR PAGAMENTO DE CONTA (O QUE JÁ EXISTIA) ---
            with aba_despesas:
                st.write("Registre aqui o dinheiro que SAIU do caixa (Pagamento da conta original).")
                with st.form("form_despesa_kit"):
                    tipo_despesa = st.radio(
                        "A conta pertence a:", 
                        ["💡 Individual (Uma Kitnet específica)", "🧱 Bloco Inteiro (Água, Luz Corredor, Manutenção)"],
                        horizontal=True
                    )
                    
                    id_kit_sel = None
                    bloco_sel = None
                    prefixo_desc = ""

                    if "Individual" in tipo_despesa:
                        if todas_kits_map:
                            nome_k = st.selectbox("Selecione a Kitnet", list(todas_kits_map.keys()))
                            id_kit_sel = todas_kits_map[nome_k]
                            prefixo_desc = f"Kitnet {nome_k}: "
                        else:
                            st.warning("⚠️ Cadastre kitnets primeiro.")
                    else:
                        if lista_apenas_blocos:
                            bloco_sel = st.selectbox("Selecione o Bloco", lista_apenas_blocos)
                            prefixo_desc = f"Bloco {bloco_sel}: "
                        else:
                            st.warning("⚠️ Nenhum bloco encontrado.")

                    st.markdown("---")
                    c1, c2 = st.columns([3, 1])
                    desc = c1.text_input("Descrição", placeholder="Ex: Conta de Água Jan/26")
                    val = c2.number_input("Valor Total da Conta (R$)", min_value=0.01, step=10.0)
                    
                    c3, c4, c5 = st.columns(3)
                    dt = c3.date_input("Data Pagamento", value=date.today())
                    banco = c4.selectbox("Saiu de qual conta?", bancos_opcoes, key="bk_d")
                    forma = c5.selectbox("Forma Pagto:", formas_opcoes, key="fm_d")
                    
                    if st.form_submit_button("Lançar Pagamento (Despesa)", type="primary"):
                        if not desc:
                            st.error("Digite uma descrição.")
                        else:
                            descricao_final = prefixo_desc + desc
                            msg = self.s_financeiro.registrar_despesa_imovel(
                                descricao=descricao_final, 
                                valor=val, 
                                id_kitnet=id_kit_sel, 
                                bloco_alvo=bloco_sel,
                                data=str(dt), 
                                banco=banco, 
                                forma=forma
                            )
                            st.success(f"✅ {msg}")

        # --- ABA 5: CADASTRO DE INQUILINOS ---
        with tab5:
            c_form, c_lista = st.columns([1, 2])
            
            with c_form:
                with st.expander("Novo Inquilino", expanded=True):
                    # Adicionado clear_on_submit=True para limpar campos após cadastro
                    with st.form("form_add_inq", clear_on_submit=True):
                        nome = st.text_input("Nome Completo *")
                        cpf_input = st.text_input("CPF", max_chars=14)
                        tel_input = st.text_input("Telefone", max_chars=15)
                        email = st.text_input("Email")
                        prof = st.text_input("Profissão")
                        
                        c1, c2 = st.columns(2)
                        sexo = c1.selectbox("Sexo", ["M", "F", "Outro"])
                        est_civil = c2.selectbox("Est. Civil", ["Solteiro", "Casado", "Divorciado", "Viúvo"])
                        obs = st.text_area("Obs")
                        
                        if st.form_submit_button("Cadastrar"):
                            erros = []
                            if not nome or len(nome.strip()) < 3:
                                erros.append("Nome obrigatório.")
                            if cpf_input and not validar_cpf(cpf_input):
                                erros.append(f"CPF inválido.")
                            if tel_input and not validar_telefone(tel_input):
                                erros.append("Telefone inválido.")
                            if email and not validar_email(email):
                                erros.append("E-mail incorreto.")

                            if erros:
                                for e in erros: st.error(f"🔴 {e}")
                            else:
                                msg = self.s_inquilino.cadastrar(
                                    nome, cpf_input, tel_input, sexo, est_civil, prof, email, obs
                                )
                                st.success(f"✅ {msg}")
                                # st.rerun() removido para manter a mensagem na tela

            with c_lista:
                st.subheader("Pessoas Cadastradas")
                lista_inq = self.s_inquilino.admin_listar_todos()
                if lista_inq:
                    dados_inq = []
                    for i in lista_inq:
                        dados_inq.append({
                            "ID": i.id_inquilino, 
                            "Nome": i.nome, 
                            "Tel": i.telefone, 
                            "CPF": i.cpf
                        })
                    st.dataframe(pd.DataFrame(dados_inq), width='stretch', hide_index=True) # <--- CORREÇÃO
                else:
                    st.info("Ninguém cadastrado.")

        # --- ABA 6: DESOCUPAÇÃO E ENCERRAMENTO ---
        with tab6:
            st.subheader("🚪 Encerrar Contrato e Liberar Kitnet")
            st.info("Aqui você encerra o contrato atual. A Kitnet voltará a ficar LIVRE. As dívidas passadas continuam registradas no sistema.")

            contratos_ativos = self.s_locacao.listar_ativas() 

            if not contratos_ativos:
                st.success("Nenhuma kitnet ocupada no momento.")
            else:
                for contrato in contratos_ativos:
                    label_contrato = f"Kitnet {contrato.get('numero')} - {contrato.get('inquilino_nome')} (Entrou em: {contrato.get('data_inicio')})"
                    
                    with st.expander(label_contrato):
                        c1, c2 = st.columns([1, 1])
                        c1.write(f"**Valor Atual:** R$ {contrato.get('valor')}")
                        c1.write(f"**Vencimento todo dia:** {contrato.get('dia_vencimento')}")
                        
                        with c2.form(key=f"form_exit_{contrato.get('id')}"):
                            st.write("🔴 **Dados do Encerramento**")
                            data_saida = st.date_input("Data da Entrega das Chaves", value=date.today())
                            
                            st.markdown("---")
                            cobrar_multa = st.checkbox("Cobrar Multa por Quebra de Contrato?", value=False)
                            valor_multa = st.number_input("Valor da Multa (R$)", value=0.0, step=100.0)
                            
                            obs_saida = st.text_area("Motivo / Observação", value="Inquilino desocupou o imóvel. Dívidas anteriores mantidas.")

                            if st.form_submit_button("Confirmar Desocupação 🚪"):
                                res = self.s_locacao.encerrar_contrato(
                                    id_locacao=contrato.get('id'),
                                    data_saida=str(data_saida),
                                    cobrar_multa=cobrar_multa,
                                    valor_multa=valor_multa
                                )
                                st.success(res)
                                st.rerun()