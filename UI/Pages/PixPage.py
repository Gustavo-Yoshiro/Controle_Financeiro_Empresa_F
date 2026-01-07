import streamlit as st

class PixPage:
    def __init__(self, pix_service, config_service):
        self.pix = pix_service
        self.cfg = config_service

    def render(self):
        st.title("💠 Carteira Pix")
        
        # 1. Carrega Bancos
        bancos_opcoes = self.cfg.listar_bancos()
        if not bancos_opcoes: bancos_opcoes = ["Outro"]

        # 2. Cadastro Rápido
        with st.expander("➕ Nova Chave Rápida"):
            with st.form("fpix"):
                c1, c2 = st.columns(2)
                t = c1.text_input("Apelido (Ex: Principal)")
                k = c2.text_input("Chave Pix")
                
                c3, c4, c5 = st.columns(3)
                b = c3.selectbox("Banco", bancos_opcoes)
                tp = c4.selectbox("Tipo", ["CPF", "CNPJ", "Email", "Celular", "Aleatória"])
                n = c5.text_input("Titular")

                if st.form_submit_button("Salvar Chave"):
                    self.pix.cadastrar_pix(t, k, tp, n, b)
                    st.success("Salva!")
                    st.rerun()

        st.divider()
        
        # 3. Listagem Inteligente
        lista = self.pix.listar_pix()
        
        if lista:
            for p in lista:
                # Destaque visual para favoritos
                borda = True
                
                with st.container(border=borda):
                    # Layout: Favorito | Dados (Copiável) | Excluir
                    c1, c2, c3 = st.columns([0.5, 4, 0.5])
                    
                    with c1:
                        # Botão de Favoritar
                        cor_fav = "⭐" if p.favorito else "☆"
                        # Use_container_width centraliza o icone
                        if st.button(cor_fav, key=f"fav_{p.id_pix}", help="Marcar como Favorito"):
                            self.pix.alternar_favorito(p.id_pix, p.favorito)
                            st.rerun()

                    with c2:
                        st.markdown(f"**{p.titulo}** | {p.banco} | *{p.titular}*")
                        # st.code gera o botão de COPIAR automaticamente!
                        st.code(p.chave, language="text")

                    with c3:
                        st.write("") # Espaço para alinhar verticalmente
                        if st.button("🗑️", key=f"del_{p.id_pix}", help="Excluir"):
                            self.pix.excluir_pix(p.id_pix)
                            st.toast("Chave removida.")
                            st.rerun()
        else:
            st.info("Nenhuma chave cadastrada. Adicione uma acima!")