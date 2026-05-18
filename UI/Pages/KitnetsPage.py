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
        
        bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
        formas_opcoes = self.cfg.listar_formas() or ["Dinheiro"]

        self.s_locacao.gerar_cobrancas_mensais()

        todas_kitnets_obj = self.s_kitnet.admin_listar_todas()
        
        kits_livres = {f"{k.identificador}-{k.numero}": k.id_kitnet for k in todas_kitnets_obj if k.status == 'LIVRE'}
        todas_kits_map = {f"{k.identificador}-{k.numero}": k.id_kitnet for k in todas_kitnets_obj}
        lista_apenas_blocos = sorted(list(set([k.identificador for k in todas_kitnets_obj])))

        contratos_ativos = self.s_locacao.dao_contrato.listar_ativos()
        ids_inq_alocados = [c.id_inquilino for c in contratos_ativos]
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Lista Geral", 
            "Novo Contrato", 
            "💰 Receber Aluguel", 
            "💸 Contas & Taxas",
            "👤 Inquilinos",
            "🚪 Desocupação / Encerrar"
        ])

        with tab1:
            with st.expander("🔎 Filtros Avançados", expanded=True):
                c_ano, c_mes, c_status, c_bloco, c_inq, c_kit = st.columns([1, 1.5, 2, 1, 2, 1.5])
                
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

                lista_blocos_filtro = ["Todos"] + lista_apenas_blocos
                filtro_bloco = c_bloco.selectbox("Bloco", lista_blocos_filtro)

                dados_tabela = self.s_relatorio.gerar_painel_geral(mes_ref=mes_ref_str)
                df = pd.DataFrame(dados_tabela)

                if not df.empty and "Identificação" in df.columns:
                    contratos_ativos = self.s_locacao.listar_ativas()
                    map_contratos = {f"{c['identificador']}-{c['numero']}": c for c in contratos_ativos}

                    inicios_reais = []
                    fins_reais = []
                    
                    for idx, row in df.iterrows():
                        ident = row["Identificação"]
                        if ident in map_contratos:
                            c_dados = map_contratos[ident]
                            
                            try:
                                dt_fmt = datetime.strptime(c_dados['data_inicio'], "%Y-%m-%d").strftime("%d/%m/%Y")
                            except:
                                dt_fmt = c_dados['data_inicio']
                            inicios_reais.append(dt_fmt)
                            
                            data_fim_raw = c_dados.get('data_fim')
                            if data_fim_raw:
                                try:
                                    dt_fim_obj = datetime.strptime(data_fim_raw, "%Y-%m-%d").date()
                                    dt_fim_fmt = dt_fim_obj.strftime("%d/%m/%Y")
                                   
                                    if dt_fim_obj < date.today():
                                        dt_fim_fmt += " (Indeterminado) 🔄"
                                except:
                                    dt_fim_fmt = data_fim_raw
                            else:
                                dt_fim_fmt = "-"
                            fins_reais.append(dt_fim_fmt)
                        else:
                            inicios_reais.append("-")
                            fins_reais.append("-")

                    df["Início Contrato"] = inicios_reais
                    df["Fim Contrato"] = fins_reais
                    
                    if "Valor" in df.columns:
                        df = df.drop(columns=["Valor"])
                    if "Valor (Contrato)" in df.columns:
                        df = df.drop(columns=["Valor (Contrato)"])

                lista_inq = ["Todos"] + list(df[df["Inquilino"] != "---"]["Inquilino"].unique()) if not df.empty else ["Todos"]
                filtro_inq = c_inq.selectbox("Inquilino", lista_inq)

                lista_kits = ["Todas"] + list(df["Identificação"].unique()) if not df.empty else ["Todas"]
                filtro_kit = c_kit.selectbox("Kitnet", lista_kits)

            if not df.empty:
                if filtro_bloco != "Todos":
                    df = df[df["Identificação"].str.startswith(f"{filtro_bloco}-")]

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
                    width='stretch',
                    hide_index=True
                )
            else:
                st.info(f"Nenhum registo encontrado para {mes_ref_str}.")

        with tab2:
            tipo = st.radio("O que deseja fazer?", ["Nova Kitnet", "Novo Contrato"], horizontal=True)
            
            if tipo == "Nova Kitnet":
                with st.expander("Cadastrar Imóvel", expanded=True):
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
                    with st.form("fc", clear_on_submit=True):
                        if not kits_livres:
                            st.warning("Não há kitnets livres no momento.")
                            k_id_sel = None
                        else:
                            nome_k = st.selectbox("Selecione a Kitnet", list(kits_livres.keys()))
                            k_id_sel = kits_livres[nome_k]

                        inq_map_bruto = self.s_inquilino.listar_simples()
                        
                       
                        inq_map = {nome: id_inq for nome, id_inq in inq_map_bruto.items() if id_inq not in ids_inq_alocados}
                        
                        if not inq_map:
                            st.warning("Não há inquilinos disponíveis (Todos já possuem contrato ou nenhum foi cadastrado).")
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
                        
                        dt_fim = c4.date_input("Data do Término (Encerramento)", value=date.today())
                        
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
                                    data_fim=str(dt_fim), 
                                    mobiliado=mob_int,
                                    obs_mobiliado=obs_mob,
                                    arquivo_upload=arquivo_contrato
                                )
                                if "Erro" in msg:
                                    st.error(msg)
                                else:
                                    st.success(msg)
                            else:
                                st.error("Preencha todos os campos obrigatórios.")

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
               
                with st.form(key=f"form_pagamento_{dados_cobranca['id_pagamento']}", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    val_sugerido = float(dados_cobranca['valor_restante'])
                    
                    valor_recebido = c1.number_input("Valor Recebido Agora (R$)", min_value=0.0, step=10.0, value=val_sugerido)
                    banco_rec = c2.selectbox("Dinheiro entrou em:", bancos_opcoes)
                    
                    arquivo_comp = st.file_uploader("Anexar Comprovante (Opcional)", type=["pdf", "png", "jpg", "jpeg"])
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
                    
                    if st.form_submit_button("Confirmar Recebimento", type="primary", width='stretch'):
                        msg = self.s_locacao.processar_pagamento_aluguel(
                            id_pagamento=dados_cobranca['id_pagamento'], 
                            valor_recebido=valor_recebido, 
                            banco=banco_rec,
                            eh_quitacao_com_desconto=eh_acordo,
                            obs=obs,
                            arquivo_comprovante=arquivo_comp 
                        )
                        if "Sucesso" in msg:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        with tab4:
            st.title("💸 Contas e Faturas")
            
            aba_taxas, aba_avulsa, aba_despesas = st.tabs([
                "💧 Rateio p/ Bloco (Água)", 
                "🙋‍♂️ Gestão de Faturas (Inquilino)",
                "🧾 Caixa da Casa (Despesa)"
            ])

            with aba_taxas:
                st.info("Adiciona o valor da água/esgoto na conta de todos os inquilinos ativos de um Bloco.")
                
                if not lista_apenas_blocos:
                    st.warning("Cadastre kitnets para ter Blocos disponíveis.")
                else:
                    with st.form("form_lanca_taxa"):
                        col_a, col_b = st.columns(2)
                        bloco_alvo = col_a.selectbox("Selecione o Bloco", lista_apenas_blocos)
                        
                        mes_taxa = date.today().month
                        ano_taxa = date.today().year
                        mes_ref_taxa = f"{ano_taxa}-{mes_taxa:02d}"
                        
                        col_b.text_input("Mês Referência (Cobrança)", value=mes_ref_taxa, disabled=True)
                        
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

            with aba_avulsa:
                st.info("Edite os valores esperados, cancele faturas geradas por engano, ou adicione novas cobranças proporcionais.")
                
                contratos_ativos = self.s_locacao.listar_ativas()
                
                if not contratos_ativos:
                    st.warning("Nenhum contrato ativo disponível.")
                else:
                    mapa_inq = {f"Kit {c['identificador']}-{c['numero']} - {c['inquilino_nome']}": c['id'] for c in contratos_ativos}
                    
                    inq_sel = st.selectbox("1. Selecione o Inquilino", list(mapa_inq.keys()))
                    id_contrato_sel = mapa_inq[inq_sel]
                    
                    st.divider()
                    
                    col_lista, col_novo = st.columns([1.5, 1])

                    with col_novo:
                        st.markdown("#### ➕ Criar Nova Fatura")
                        with st.form("form_divida_indiv", clear_on_submit=True):
                            desc_divida = st.text_input("Motivo / Descrição", placeholder="Ex: Proporcional 15 dias, Multa...")
                            val_divida = st.number_input("Valor (R$)", min_value=0.01, step=10.0)
                            
                            hoje = date.today()
                            mes_ref_div = st.text_input("Mês de Referência (YYYY-MM)", value=f"{hoje.year}-{hoje.month:02d}")
                            
                            if st.form_submit_button("Lançar Cobrança",  width='stretch'):
                                if not desc_divida:
                                    st.error("Digite o motivo.")
                                else:
                                    msg = self.s_locacao.lancar_divida_avulsa_individual(
                                        id_contrato=id_contrato_sel, 
                                        valor=val_divida, 
                                        mes_ref=mes_ref_div, 
                                        descricao=desc_divida
                                    )
                                    if "Sucesso" in msg: st.success(msg); st.rerun()
                                    else: st.warning(msg)

                    with col_lista:
                        st.markdown("#### 📋 Faturas do Inquilino")
                        faturas_inq = self.s_locacao.listar_faturas_por_contrato(id_contrato_sel)
                        
                        if not faturas_inq:
                            st.caption("Nenhuma fatura registada para este contrato.")
                        else:
                            faturas_ativas = [f for f in faturas_inq if f['status'] != 'cancelado']
                            if faturas_ativas:
                                with st.expander("🛠️ Ações em Massa (Cancelar Várias)", expanded=False):
                                    with st.form("form_bulk_cancel", clear_on_submit=True):
                                        mapa_bulk = {f"Mês: {f['mes_referencia']} | R$ {f['valor_esperado']:.2f} ({f['status'].upper()})": f['id_pagamento'] for f in faturas_ativas}
                                        fats_selecionadas = st.multiselect("Selecione as faturas que deseja CANCELAR:", list(mapa_bulk.keys()))
                                        
                                        if st.form_submit_button("🗑️ Cancelar Selecionadas", type="primary",  width='stretch'):
                                            if not fats_selecionadas:
                                                st.warning("Selecione pelo menos uma fatura para cancelar.")
                                            else:
                                                for f_label in fats_selecionadas:
                                                    self.s_locacao.deletar_fatura(mapa_bulk[f_label])
                                                st.success(f"{len(fats_selecionadas)} faturas canceladas com sucesso!")
                                                st.rerun()
                                st.markdown("---")

                            for f in faturas_inq:
                                if f['status'] == 'pago': status_icone = "🟢 PAGO"
                                elif f['status'] == 'parcial': status_icone = "🟠 PARCIAL"
                                elif f['status'] == 'cancelado': status_icone = "⚫ CANCELADA"
                                else: status_icone = "🔴 PENDENTE"
                                
                                with st.expander(f"Mês: {f['mes_referencia']} | {status_icone} | R$ {f['valor_esperado']:.2f}"):
                                    st.caption(f"**Já pago:** R$ {f['valor_pago']:.2f}")
                                    
                                    c_edt1, c_edt2 = st.columns(2)
                                    n_val = c_edt1.number_input("Editar Valor (R$)", value=float(f['valor_esperado']), key=f"val_{f['id_pagamento']}")
                                    n_obs = c_edt2.text_input("Observação", value=f['obs'] or "", key=f"obs_{f['id_pagamento']}")
                                    
                                    c_btn1, c_btn2 = st.columns(2)
                                    if c_btn1.button("💾 Salvar Edição", key=f"save_{f['id_pagamento']}", width='stretch'):
                                        msg = self.s_locacao.atualizar_fatura(f['id_pagamento'], n_val, n_obs)
                                        st.success(msg)
                                        st.rerun()
                                        
                                    if f['status'] != 'cancelado':
                                        if c_btn2.button("🗑️ Cancelar Fatura", type="primary", key=f"del_{f['id_pagamento']}",  width='stretch'):
                                            msg = self.s_locacao.deletar_fatura(f['id_pagamento'])
                                            st.toast(msg)
                                            st.rerun()

            with aba_despesas:
                st.write("Registre aqui o dinheiro que SAIU do caixa para a manutenção ou contas da Kitnet.")
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

        with tab5:
            c_form, c_lista = st.columns([1, 2])
            
            with c_form:
                with st.expander("Novo Inquilino", expanded=True):
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
                    st.dataframe(pd.DataFrame(dados_inq), width='stretch', hide_index=True)
                else:
                    st.info("Ninguém cadastrado.")

        with tab6:
            st.subheader("⚙️ Gestão de Contratos Ativos")
            st.info("Edite as informações do contrato (datas, valores) ou encerre-o para libertar a Kitnet.")

            contratos_ativos = self.s_locacao.listar_ativas() 

            if not contratos_ativos:
                st.success("Nenhuma kitnet ocupada no momento.")
            else:
                for contrato in contratos_ativos:
                    data_inicio_fmt = contrato.get('data_inicio')
                    try: data_inicio_fmt = datetime.strptime(contrato.get('data_inicio'), "%Y-%m-%d").strftime("%d/%m/%Y")
                    except: pass
                    
                    label_contrato = f"Kitnet {contrato.get('numero')} - {contrato.get('inquilino_nome')} (Início: {data_inicio_fmt})"
                    
                    with st.expander(label_contrato):
                        aba_edit, aba_encerra = st.tabs(["✏️ Editar Dados", "🚪 Encerrar Contrato"])
                        
                        with aba_edit:
                            with st.form(key=f"form_edit_{contrato.get('id')}"):
                                st.write("Altere os dados abaixo e guarde para atualizar o contrato em vigor.")
                                c1, c2 = st.columns(2)
                                novo_val = c1.number_input("Valor do Aluguer (R$)", min_value=0.0, value=float(contrato.get('valor', 0.0)))
                                novo_venc = c2.number_input("Dia de Vencimento", min_value=1, max_value=31, value=int(contrato.get('dia_vencimento', 10)))
                                
                                c3, c4 = st.columns(2)
                                dt_ini_str = contrato.get('data_inicio')
                                try: dt_ini_obj = datetime.strptime(dt_ini_str, "%Y-%m-%d").date() if dt_ini_str else date.today()
                                except: dt_ini_obj = date.today()
                                
                                dt_fim_str = contrato.get('data_fim')
                                try: dt_fim_obj = datetime.strptime(dt_fim_str, "%Y-%m-%d").date() if dt_fim_str else date.today()
                                except: dt_fim_obj = date.today()
                                
                                nova_dt_ini = c3.date_input("Data de Início", value=dt_ini_obj)
                                nova_dt_fim = c4.date_input("Data de Fim", value=dt_fim_obj)
                                
                                if st.form_submit_button("💾 Guardar Alterações", type="primary",  width='stretch'):
                                   
                                    cont_obj = self.s_locacao.dao_contrato.buscar_por_id(contrato.get('id'))
                                    if cont_obj:
                                        cont_obj.valor_fechado = novo_val
                                        cont_obj.data_vencimento = novo_venc
                                        cont_obj.data_inicio = str(nova_dt_ini)
                                        cont_obj.data_fim = str(nova_dt_fim)
                                        self.s_locacao.dao_contrato.salvar(cont_obj)
                                        st.success("Contrato atualizado com sucesso!")
                                        st.rerun()
                                    else:
                                        st.error("Erro ao encontrar o contrato na base de dados.")

                        with aba_encerra:
                            with st.form(key=f"form_exit_{contrato.get('id')}"):
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