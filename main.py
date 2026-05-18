import streamlit as st
from Persistencia.Banco import BancoDeDados
from UI.App import AppInterface
from Utils.PopulacaoInicial import PopulacaoInicial
import os

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Gestão Família Enterprise",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def inicializar_sistema():
    """
    Roda apenas uma vez quando o servidor sobe.
    Se o banco 'finanças.db' não existir, cria e popula.
    """
    bd = BancoDeDados()
    caminho_banco = "financas.db"  

    if not os.path.exists(caminho_banco):
        st.write("📂 Banco 'finanças.db' não encontrado. Criando...")
        bd.criarBanco()

        populador = PopulacaoInicial()
        populador.popular_tudo()
        st.write("✅ Banco criado e populado com dados iniciais.")
    else:
        st.write("✔️ Banco 'finanças.db' já existe. Pulando criação.")
        print('Banco carregado!')

    return True

def main():
    inicializar_sistema()
    app = AppInterface()
    app.run()

if __name__ == "__main__":
    main()
