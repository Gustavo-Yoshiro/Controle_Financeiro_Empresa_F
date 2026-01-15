import streamlit as st
from datetime import date, timedelta

class DividasPage:
    def __init__(self, boleto_service, emprestimo_service, config_service, credito_service):
        self.bol = boleto_service
        self.emp = emprestimo_service
        self.cfg = config_service 
        self.cred = credito_service # <--- Novo Serviço Injetado

    def render(self):
        st.title("💸 Gestão de Dívidas")
        
        # Abas Principais
        tab_boletos, tab_cartao, tab_emprestimos = st.tabs([
            "🧾 Boletos Avulsos", 
            "💳 Cartão de Crédito", 
            "🏦 Empréstimos"
        ])

        # =====================================================================
        # ABA 1: BOLETOS (CONTAS AVULSAS)
        # =====================================================================
        with tab_boletos:
            bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
            cats_dicts = self.cfg.listar_categorias()
            mapa_cats = {c['nome']: c['id'] for c in cats_dicts}

            # Totais
            try:
                totais = self.bol.calcular_totais()
                st.metric("Total Pendente (Boletos Avulsos)", f"R$ {totais['total_geral']:.2f}")
            except: pass

            # Form novo boleto
            with st.expander("➕ Agendar Nova Conta (Água, Luz...)", expanded=False):
                with st.form("form_novo_boleto", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    d = c1.text_input("Descrição (Ex: Luz)")
                    nome_cat = c1.selectbox("Categoria", list(mapa_cats.keys()))
                    v = c2.number_input("Valor (R$)", min_value=0.0)
                    dt = c2.date_input("Vencimento")
                    c = st.text_input("Código de Barras")
                    
                    if st.form_submit_button("Agendar"):
                        self.bol.cadastrar_boleto(d, v, str(dt), mapa_cats.get(nome_cat, 2), c)
                        st.success("Conta agendada!")
                        st.rerun()

            st.divider()
            
            # Lista apenas boletos que NÃO são de cartão
            boletos = self.bol.listar_boletos_detalhados()
            
            if boletos:
                for b in boletos:
                    with st.container(border=True):
                        cols = st.columns([3, 2, 1.5])
                        
                        with cols[0]:
                            st.markdown(f"**{b['descricao']}**")
                            st.caption(f"Cat: {b.get('categoria','-')} | Vence: {b['vencimento_br']}")
                            
                            cod = b.get('codigo_barras')
                            if cod and len(cod) > 5: st.code(cod, language="text")
                                
                            if "ATRASADO" in b['status_texto']: st.error(b['status_texto'])
                            else: st.info(b['status_texto'])
                        
                        with cols[1]:
                            st.write("") 
                            banco_escolhido = st.selectbox("Pagar com:", bancos_opcoes, key=f"bk_{b['id']}", label_visibility="collapsed")
                        
                        with cols[2]:
                            st.markdown(f"### R$ {b['valor']:.2f}")
                            if st.button("✅ Pagar", key=f"btn_{b['id']}", width='stretch'):
                                msg = self.bol.pagar_boleto(b['id'], banco_escolhido)
                                st.toast(msg)
                                st.rerun()
            else:
                st.success("Tudo pago nos boletos avulsos! 🎉")

        # =====================================================================
        # ABA 2: CARTÃO DE CRÉDITO (A GRANDE MUDANÇA)
        # =====================================================================
        with tab_cartao:
            # Sub-abas para organizar o fluxo do cartão
            sub_faturas, sub_compra, sub_config = st.tabs(["🧾 Pagar Faturas", "🛍️ Lançar Compra", "⚙️ Configurar Cartões"])

            # --- SUB 1: VISUALIZAR E PAGAR (O que já existia) ---
            with sub_faturas:
                st.caption("Aqui suas compras são agrupadas automaticamente por Vencimento e Cartão.")
                
                # Pega os dados agrupados do CreditoService (mudou de lugar)
                faturas = self.cred.listar_faturas_agrupadas()
                bancos_opcoes_pag = self.cfg.listar_bancos() or ["Dinheiro"]
                
                if faturas:
                    chaves_ordenadas = sorted(faturas.keys())
                    for chave in chaves_ordenadas:
                        fatura = faturas[chave]
                        total_fatura = fatura['total']
                        itens = fatura['itens']
                        venc_br = fatura['vencimento_br']
                        nome_banco = fatura['banco']
                        
                        icone = "💳"
                        if "Nubank" in nome_banco: icone = "🟣"
                        elif "Inter" in nome_banco: icone = "🟠"
                        elif "Itaú" in nome_banco: icone = "🟠"
                        elif "Santander" in nome_banco: icone = "🔴"

                        with st.container(border=True):
                            c_topo1, c_topo2 = st.columns([3, 1.5])
                            c_topo1.subheader(f"{icone} Fatura {nome_banco}")
                            c_topo1.caption(f"Vencimento: **{venc_br}** | {len(itens)} compras")
                            c_topo2.metric("Valor Total", f"R$ {total_fatura:,.2f}")
                            
                            st.divider()
                            
                            c_pg1, c_pg2 = st.columns([3, 1])
                            banco_pagador = c_pg1.selectbox(f"Pagar fatura {nome_banco} usando:", bancos_opcoes_pag, key=f"pg_{chave}")
                            
                            if c_pg2.button("💸 Pagar Fatura", key=f"btn_fat_{chave}", width='stretch', type="primary"):
                                msg = self.cred.pagar_fatura_inteira(chave, banco_pagador, total_fatura)
                                st.success(msg)
                                st.balloons()
                                st.rerun()
                            
                            with st.expander("🔎 Ver itens desta fatura"):
                                dados_tabela = [{"Descrição": i.descricao, "Valor": f"R$ {i.valor:.2f}", "Data Original": i.data_vencimento} for i in itens]
                                st.table(dados_tabela)
                else:
                    st.info("Nenhuma fatura de cartão em aberto.")

            # --- SUB 2: LANÇAR COMPRA (Lógica do CreditoService) ---
            with sub_compra:
                st.caption("Use este formulário para compras parceladas. O sistema gera as faturas futuras.")
                
                cartoes_disponiveis = self.cred.listar_nomes_cartoes()
                
                if not cartoes_disponiveis:
                    st.warning("⚠️ Cadastre um cartão na aba 'Configurar Cartões' primeiro.")
                else:
                    with st.form("form_compra_credito", clear_on_submit=True):
                        c1, c2 = st.columns(2)
                        cartao_sel = c1.selectbox("Cartão Utilizado", cartoes_disponiveis)
                        dt_compra = c2.date_input("Data da Compra", value=date.today())
                        
                        # --- VISUALIZAÇÃO DO LIMITE ---
                        # Chama o serviço para pegar o limite do cartão selecionado
                        info_limite = self.cred.get_info_limite(cartao_sel)
                        
                        if info_limite['total'] > 0:
                            percentual = min(info_limite['usado'] / info_limite['total'], 1.0)
                            st.progress(percentual, text=f"Limite Utilizado: R$ {info_limite['usado']:,.2f} / R$ {info_limite['total']:,.2f}")
                            st.caption(f"🟢 **Disponível: R$ {info_limite['disponivel']:,.2f}**")
                        else:
                            st.caption("ℹ️ Este cartão não possui limite configurado.")
                        # -----------------------------

                        desc = st.text_input("Descrição", placeholder="Ex: Notebook, Jantar...")
                        
                        c3, c4, c5 = st.columns(3)
                        val_total = c3.number_input("Valor TOTAL (R$)", min_value=0.01, step=10.0)
                        parcelas = c4.number_input("Parcelas", min_value=1, max_value=24, value=1)
                        
                        cats = self.cfg.listar_categorias()
                        cats = [c for c in cats if c.get('tipo') == 'despesa']
                        mapa_cats = {c['nome']: c['id'] for c in cats}
                        nome_cat = c5.selectbox("Categoria", list(mapa_cats.keys()))
                        
                        if parcelas > 1 and val_total > 0:
                            st.info(f"ℹ️ Serão {parcelas}x de **R$ {val_total/parcelas:.2f}**")

                        if st.form_submit_button("🚀 Lançar Compra"):
                            if not desc:
                                st.error("Digite uma descrição.")
                            else:
                                msg = self.cred.registrar_compra_inteligente(
                                    descricao=desc,
                                    valor_total=val_total,
                                    data_compra_str=str(dt_compra),
                                    id_categoria=mapa_cats.get(nome_cat, 2),
                                    nome_cartao=cartao_sel,
                                    parcelas=int(parcelas)
                                )
                                if "Sucesso" in msg:
                                    st.success(msg)
                                    st.rerun() # Atualiza para mostrar nas faturas
                                else:
                                    st.error(msg) # Mostra o erro de limite se houver

            # --- SUB 3: CONFIGURAR (Cadastro de Cartões) ---
            with sub_config:
                st.caption("Cadastre seus cartões e datas de fechamento.")
                with st.form("form_novo_cartao", clear_on_submit=True):
                    c_nome, c_band = st.columns(2)
                    nome = c_nome.text_input("Apelido (Ex: Nubank)")
                    bandeira = c_band.selectbox("Bandeira", ["Mastercard", "Visa", "Elo", "Amex", "Outro"])
                    
                    c_fech, c_venc, c_lim = st.columns(3)
                    dia_fech = c_fech.number_input("Dia Fechamento", 1, 31, value=4)
                    dia_venc = c_venc.number_input("Dia Vencimento", 1, 31, value=11)
                    limite = c_lim.number_input("Limite (Opcional)", 0.0)
                    
                    if st.form_submit_button("Salvar Configuração"):
                        msg = self.cred.cadastrar_config_cartao(nome, dia_fech, dia_venc, limite, bandeira)
                        if "Sucesso" in msg:
                            st.success(msg)
                            st.rerun() # <--- O SEGREDO: Atualiza a página para o cartão aparecer na lista
                        else:
                            st.error(msg)
                
                st.divider()
                st.write("#### Cartões Ativos")
                lista = self.cred.listar_nomes_cartoes()
                if lista:
                    for cartao in lista: st.text(f"💳 {cartao}")

        # =====================================================================
        # ABA 3: EMPRÉSTIMOS (MANTIDO IGUAL)
        # =====================================================================
        with tab_emprestimos:
            bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
            
            st.info("ℹ️ Ao contratar, o dinheiro entra no caixa hoje e as parcelas são geradas.")

            with st.expander("➕ Contratar Novo Empréstimo"):
                with st.form("form_emp", clear_on_submit=True):
                    desc = st.text_input("Descrição")
                    c1, c2, c3 = st.columns(3)
                    v_rec = c1.number_input("Valor Recebido", 100.0)
                    v_parc = c2.number_input("Valor Parcela", 10.0)
                    qtd = c3.number_input("Qtd", 1)
                    
                    c4, c5 = st.columns(2)
                    hoje = date.today()
                    dt_lib = c4.date_input("Data Liberação", value=hoje)
                    dt_pri = c4.date_input("Data 1ª Parcela", value=hoje + timedelta(days=30))
                    bk = c5.selectbox("Banco", bancos_opcoes)
                    
                    if st.form_submit_button("Confirmar Contrato"):
                        try:
                            msg = self.emp.contratar_emprestimo(
                                desc, v_rec, v_parc, int(qtd), 
                                str(dt_lib), str(dt_pri), bk
                            )
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        except Exception as e: st.error(e)

            st.divider()
            lista = self.emp.listar_emprestimos()
            if lista:
                for e in lista:
                    if e.status == 'ativo':
                        falta = e.valor_total - e.valor_pago
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 1.5])
                            c1.markdown(f"### 🏦 {e.descricao}")
                            c1.write(f"Parcela: R$ {e.valor_parcela:.2f} ({e.qtd_parcelas}x)")
                            c1.caption(f"Início: {e.data_inicio} | 1ª Parc: {e.data_primeira_parcela}")
                            c2.metric("Saldo Devedor", f"R$ {falta:,.2f}", delta="-Pendente", delta_color="inverse")
            else:
                st.info("Nenhum empréstimo ativo.")