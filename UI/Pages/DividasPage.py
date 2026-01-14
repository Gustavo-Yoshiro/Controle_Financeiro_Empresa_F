import streamlit as st
from datetime import date, timedelta

class DividasPage:
    def __init__(self, boleto_service, emprestimo_service, config_service):
        self.bol = boleto_service
        self.emp = emprestimo_service
        self.cfg = config_service 

    def render(self):
        st.title("💸 Gestão de Dívidas")
        
        # AGORA SÃO 3 ABAS
        tab_boletos, tab_faturas, tab_emprestimos = st.tabs(["🧾 Contas a Pagar", "💳 Faturas Cartão", "🏦 Empréstimos"])

        # =====================================================================
        # ABA 1: BOLETOS (CONTAS AVULSAS)
        # =====================================================================
        with tab_boletos:
            bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
            cats_dicts = self.cfg.listar_categorias()
            mapa_cats = {c['nome']: c['id'] for c in cats_dicts}

            # Totais
            try:
                # O service já calcula separando faturas de boletos se atualizado
                totais = self.bol.calcular_totais()
                st.metric("Total Pendente (Boletos Avulsos)", f"R$ {totais['total_geral']:.2f}")
            except: 
                pass

            # Form novo boleto
            with st.expander("➕ Agendar Nova Conta", expanded=False):
                with st.form("form_novo_boleto"):
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
                            
                            # Código de Barras
                            cod = b.get('codigo_barras')
                            if cod and len(cod) > 5: st.code(cod, language="text")
                                
                            if "ATRASADO" in b['status_texto']: st.error(b['status_texto'])
                            else: st.info(b['status_texto'])
                        
                        with cols[1]:
                            st.write("") 
                            banco_escolhido = st.selectbox("Pagar com:", bancos_opcoes, key=f"bk_{b['id']}", label_visibility="collapsed")
                        
                        with cols[2]:
                            st.markdown(f"### R$ {b['valor']:.2f}")
                            if st.button("✅ Pagar", key=f"btn_{b['id']}", use_container_width=True):
                                msg = self.bol.pagar_boleto(b['id'], banco_escolhido)
                                st.toast(msg)
                                st.rerun()
            else:
                st.success("Tudo pago nos boletos avulsos! 🎉")

        # =====================================================================
        # ABA 2: FATURAS DE CARTÃO (NOVIDADE!)
        # =====================================================================
        with tab_faturas:
            st.info("Aqui suas compras são agrupadas automaticamente por Data de Vencimento e Banco.")
            
            # Pega os dados agrupados do Service
            faturas = self.bol.listar_faturas_agrupadas()
            
            if faturas:
                # Ordena as chaves para mostrar as datas mais próximas primeiro
                chaves_ordenadas = sorted(faturas.keys())
                
                for chave in chaves_ordenadas:
                    fatura = faturas[chave]
                    total_fatura = fatura['total']
                    itens = fatura['itens']
                    venc_br = fatura['vencimento_br']
                    nome_banco = fatura['banco'] # Ex: "Nubank", "Inter"
                    
                    # Definição visual baseada no banco
                    icone = "💳"
                    if "Nubank" in nome_banco: icone = "🟣" # Roxo
                    elif "Inter" in nome_banco: icone = "🟠" # Laranja
                    elif "Caixa" in nome_banco: icone = "🔵" # Azul
                    elif "Bradesco" in nome_banco: icone = "🔴" # Vermelho
                    elif "Itaú" in nome_banco: icone = "🟠" # Laranja
                    elif "Santander" in nome_banco: icone = "🔴" # Vermelho

                    # Renderiza o Card da Fatura
                    with st.container(border=True):
                        c_topo1, c_topo2 = st.columns([3, 1.5])
                        
                        c_topo1.subheader(f"{icone} Fatura {nome_banco}")
                        c_topo1.caption(f"Vencimento: **{venc_br}** | {len(itens)} compras agendadas")
                        
                        c_topo2.metric("Valor Total", f"R$ {total_fatura:,.2f}")
                        
                        st.divider()
                        
                        # Área de Pagamento
                        c_pg1, c_pg2 = st.columns([3, 1])
                        banco_pagador = c_pg1.selectbox(f"Pagar fatura {nome_banco} usando:", bancos_opcoes, key=f"pg_{chave}")
                        
                        if c_pg2.button("💸 Pagar Fatura", key=f"btn_fat_{chave}", use_container_width=True, type="primary"):
                            # Chama o método que paga TUDO de uma vez
                            msg = self.bol.pagar_fatura_inteira(chave, banco_pagador, total_fatura)
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        
                        # Detalhamento (Sanfona)
                        with st.expander("🔎 Ver itens desta fatura"):
                            dados_tabela = []
                            for item in itens:
                                dados_tabela.append({
                                    "Descrição": item.descricao,
                                    "Valor": f"R$ {item.valor:.2f}",
                                    "Data Original": item.data_vencimento # Ou data de criação se tivesse
                                })
                            st.table(dados_tabela)
            else:
                st.info("Nenhuma fatura de cartão em aberto. Parabéns!")

        # =====================================================================
        # ABA 3: EMPRÉSTIMOS (MANTIDO IGUAL)
        # =====================================================================
        with tab_emprestimos:
            bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
            
            st.info("ℹ️ Ao contratar, o dinheiro entra no caixa hoje e as parcelas são geradas.")

            with st.expander("➕ Contratar Novo Empréstimo"):
                with st.form("form_emp"):
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
                    
                    total_pagar = v_parc * qtd
                    st.caption(f"Entra: R$ {v_rec:.2f} | Sai: R$ {total_pagar:.2f}")

                    if st.form_submit_button("Confirmar Contrato"):
                        try:
                            msg = self.emp.contratar_emprestimo(
                                desc, v_rec, v_parc, int(qtd), 
                                str(dt_lib), str(dt_pri), bk
                            )
                            st.success(msg); st.balloons(); st.rerun()
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