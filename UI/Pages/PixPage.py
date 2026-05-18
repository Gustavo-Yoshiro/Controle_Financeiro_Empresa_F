import streamlit as st
import string 
from Utils.Validadores import validar_cpf, validar_telefone, validar_cnpj, validar_email

class PixPage:
    def __init__(self, pix_service, config_service):
        self.pix = pix_service
        self.cfg = config_service

    def render(self):
        st.title("💠 Carteira Pix")
        
        
        lista_completa = self.pix.listar_pix()
        
        st.sidebar.header("🗂️ Filtros Pix")
        
        alfabeto = ["Todos"] + list(string.ascii_uppercase)
        filtro_letra = st.sidebar.selectbox("Filtrar por letra inicial (Apelido):", alfabeto)
        
        col_search, col_stats = st.columns([3, 1])
        with col_search:
            termo_busca = st.text_input("🔍 Pesquisar chaves...", placeholder="Busque por apelido ou titular")
        
        with col_stats:
            st.caption(f"Total: {len(lista_completa)} chaves")
        
        bancos_opcoes = self.cfg.listar_bancos()
        if not bancos_opcoes: bancos_opcoes = ["Outro"]

        with st.expander("➕ Nova Chave Rápida", expanded=False):
            with st.form("fpix"):
                c1, c2 = st.columns(2)
                t = c1.text_input("Apelido (Ex: Principal)")
                k = c2.text_input("Chave Pix")
                
                c3, c4, c5 = st.columns(3)
                b = c3.selectbox("Banco", bancos_opcoes)
                tp = c4.selectbox("Tipo", ["CPF", "CNPJ", "Email", "Celular", "Aleatória"])
                n = c5.text_input("Titular")

                if st.form_submit_button("Salvar Chave"):
                    erro = None
                    if not k:
                        erro = "A Chave Pix é obrigatória."
                    elif tp == "CPF" and not validar_cpf(k):
                        erro = f"O CPF '{k}' é inválido."
                    elif tp == "CNPJ" and not validar_cnpj(k):
                        erro = f"O CNPJ '{k}' é inválido."
                    elif tp == "Celular" and not validar_telefone(k):
                        erro = "Celular inválido (Use DDD+Número)."
                    elif tp == "Email" and not validar_email(k):
                        erro = "E-mail inválido."
                    
                
                    if erro:
                        st.error(f"🔴 {erro}")
                    else:
                        msg_retorno = self.pix.cadastrar_pix(t, k, tp, n, b)
                        
                        if "Erro" in msg_retorno:
                            st.warning(f"⚠️ {msg_retorno}")  
                        else:
                            st.success(f"✅ {msg_retorno}") 
                            st.rerun()

        st.divider()
        
        #  APLICAÇÃO DOS FILTROS NA LISTA
        
        lista_filtrada = lista_completa

        if termo_busca:
            termo = termo_busca.lower()
            lista_filtrada = [
                p for p in lista_filtrada 
                if termo in p.titulo.lower() or termo in p.titular.lower()
            ]

        if filtro_letra != "Todos":
            lista_filtrada = [
                p for p in lista_filtrada 
                if p.titulo and p.titulo[0].upper() == filtro_letra
            ]

        #  RENDERIZAÇÃO DA LISTA
        
        if lista_filtrada:
            lista_filtrada.sort(key=lambda x: x.favorito, reverse=True)

            for p in lista_filtrada:
                borda = True
                
                with st.container(border=borda):
                    c1, c2, c3 = st.columns([0.5, 4, 0.5])
                    
                    with c1:
                        cor_fav = "⭐" if p.favorito else "☆"
                        
                        if st.button(cor_fav, key=f"fav_{p.id_pix}", help="Clique para Favoritar"):
                            novo_status = 1 if p.favorito == 0 else 0
                            
                            self.pix.alternar_favorito(p.id_pix, novo_status)
                            st.rerun()

                    with c2:
                        icone_tipo = "🏢" if p.tipo == "CNPJ" else "👤" if p.tipo == "CPF" else "📱" if p.tipo == "Celular" else "📧"
                        
                        titulo_display = f"**{p.titulo}**" if not p.favorito else f"**:orange[{p.titulo}]**"
                        
                        st.markdown(f"{titulo_display} | {icone_tipo} {p.banco} | *{p.titular}*")
                        st.code(p.chave, language="text")

                    with c3:
                        st.write("") 
                        if st.button("🗑️", key=f"del_{p.id_pix}", help="Excluir Chave"):
                            self.pix.excluir_pix(p.id_pix)
                            st.toast("Chave removida.")
                            st.rerun()
        else:
            if not lista_completa:
                st.info("Nenhuma chave cadastrada. Use o formulário acima.")
            else:
                st.warning("Nenhuma chave encontrada com esses filtros.")