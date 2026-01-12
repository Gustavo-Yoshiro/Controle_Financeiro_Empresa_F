import streamlit as st
from datetime import date, timedelta

class DividasPage:
    def __init__(self, boleto_service, emprestimo_service, config_service):
        self.bol = boleto_service
        self.emp = emprestimo_service
        self.cfg = config_service 

    def render(self):
        st.title("💸 Gestão de Dívidas")
        
        # Criação das Abas
        tab_boletos, tab_emprestimos = st.tabs(["🧾 Contas a Pagar", "🏦 Empréstimos & Financiamentos"])

        # =====================================================================
        # ABA 1: BOLETOS (CONTAS A PAGAR)
        # =====================================================================
        with tab_boletos:
            # 1. Carrega Dados Auxiliares
            bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
            cats_dicts = self.cfg.listar_categorias()
            mapa_cats = {c['nome']: c['id'] for c in cats_dicts}

            # 2. Mostra Totais do Mês/Geral
            try:
                totais = self.bol.calcular_totais()
                c1, c2 = st.columns(2)
                c1.metric("Total Pendente Geral", f"R$ {totais['total_geral']:.2f}")
            except:
                st.metric("Total Pendente", "R$ 0.00")

            # --- FORMULÁRIO NOVO BOLETO ---
            with st.expander("➕ Agendar Nova Conta / Boleto", expanded=False):
                with st.form("form_novo_boleto"):
                    col1, col2 = st.columns(2)
                    with col1:
                        d = st.text_input("Descrição (Ex: Luz, Internet)")
                        nome_cat = st.selectbox("Categoria", list(mapa_cats.keys()))
                    with col2:
                        v = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
                        dt = st.date_input("Vencimento")
                    
                    c = st.text_input("Código de Barras (Opcional)")
                    
                    if st.form_submit_button("Agendar Pagamento"):
                        if not d or v <= 0:
                            st.warning("Preencha descrição e valor.")
                        else:
                            id_cat = mapa_cats.get(nome_cat, 2)
                            self.bol.cadastrar_boleto(d, v, str(dt), id_cat, c)
                            st.success("Conta agendada!")
                            st.rerun()

            st.divider()
            
            # --- LISTAGEM DE PENDÊNCIAS ---
            st.subheader("Fila de Pagamentos")
            boletos = self.bol.listar_boletos_detalhados()
            
            if boletos:
                for b in boletos:
                    with st.container(border=True):
                        cols = st.columns([3, 2, 1.5])
                        
                        # Info da Conta
                        with cols[0]:
                            st.markdown(f"**{b['descricao']}**")
                            st.caption(f"Cat: {b.get('categoria', '-')} | Vence: {b['vencimento_br']}")
                            
                            # --- NOVIDADE: CÓDIGO DE BARRAS COPIÁVEL ---
                            # Se tiver código, mostra o widget de copiar
                            cod_barras = b.get('codigo_barras')
                            if cod_barras and len(cod_barras) > 5:
                                # st.code gera o botão de copiar automaticamente
                                st.code(cod_barras, language="text")
                            # -------------------------------------------

                            if "ATRASADO" in b['status_texto']:
                                st.error(b['status_texto'])
                            else:
                                st.info(b['status_texto'])
                        
                        # Seleção de Banco
                        with cols[1]:
                            st.write("") 
                            banco_escolhido = st.selectbox(
                                "Pagar com:", 
                                bancos_opcoes, 
                                key=f"bk_{b['id']}",
                                label_visibility="collapsed"
                            )
                        
                        # Botão Pagar
                        with cols[2]:
                            st.markdown(f"### R$ {b['valor']:.2f}")
                            if st.button("✅ Pagar", key=f"btn_{b['id']}", use_container_width=True):
                                msg = self.bol.pagar_boleto(b['id'], banco_escolhido)
                                st.toast(msg)
                                st.rerun()
            else:
                st.success("Tudo pago! Você está livre de boletos por enquanto. 🎉")

        # =====================================================================
        # ABA 2: EMPRÉSTIMOS
        # =====================================================================
        with tab_emprestimos:
            bancos_opcoes = self.cfg.listar_bancos() or ["Dinheiro"]
            
            st.info("ℹ️ Ao contratar um empréstimo aqui, o dinheiro entra no caixa hoje e as parcelas são geradas automaticamente.")

            with st.expander("➕ Contratar Novo Empréstimo", expanded=False):
                with st.form("form_emp"):
                    desc = st.text_input("Descrição (Ex: Financiamento Carro)")
                    
                    c1, c2, c3 = st.columns(3)
                    v_recebido = c1.number_input("Valor Recebido (Líquido)", min_value=100.0, step=100.0)
                    v_parc = c2.number_input("Valor da Parcela (R$)", min_value=10.0, step=10.0)
                    qtd = c3.number_input("Qtd Parcelas", min_value=1, step=1)
                    
                    # --- DATAS ---
                    c4, c5 = st.columns(2)
                    hoje = date.today()
                    
                    dt_liberacao = c4.date_input("Data Liberação (Dinheiro)", value=hoje)
                    dt_primeira = c4.date_input("Data 1ª Parcela", value=hoje + timedelta(days=30))
                    
                    banco = c5.selectbox("Onde caiu o dinheiro?", bancos_opcoes)
                    
                    # Simulação Visual
                    total_pagar = v_parc * qtd
                    juros_totais = total_pagar - v_recebido
                    
                    st.caption(f"💰 **Resumo:** Entra **R$ {v_recebido:.2f}** | Sai **R$ {total_pagar:.2f}** (Juros: R$ {juros_totais:.2f})")
                    
                    if st.form_submit_button("✅ Confirmar Contrato"):
                        try:
                            msg = self.emp.contratar_emprestimo(
                                descricao=desc, 
                                valor_pego=v_recebido, 
                                valor_parcela=v_parc, 
                                qtd_parcelas=int(qtd), 
                                data_liberacao=str(dt_liberacao), 
                                data_primeira_parcela=str(dt_primeira), 
                                banco=banco
                            )
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

            st.divider()
            st.subheader("Contratos Ativos")
            
            lista = self.emp.listar_emprestimos()
            if lista:
                for e in lista:
                    if e.status == 'ativo':
                        # Calculando dívida real
                        divida_total = e.valor_total
                        ja_pago = e.valor_pago
                        falta = divida_total - ja_pago
                        
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 1.5])
                            with c1:
                                st.markdown(f"### 🏦 {e.descricao}")
                                st.write(f"Valor Original: **R$ {divida_total:.2f}**")
                                st.write(f"Parcela: **R$ {e.valor_parcela:.2f}** ({e.qtd_parcelas}x)")
                                st.caption(f"Início: {e.data_inicio} | 1ª Parc: {e.data_primeira_parcela}")
                            
                            with c2:
                                st.metric("Saldo Devedor", f"R$ {falta:,.2f}", delta="-Pendente", delta_color="inverse")
                                st.caption(f"Já pago: R$ {ja_pago:,.2f}")
            else:
                st.info("Nenhum empréstimo ativo.")