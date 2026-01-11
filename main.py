import streamlit as st
from Persistencia.Banco import BancoDeDados
from UI.App import AppInterface

from Utils.PopulacaoInicial import PopulacaoInicial 

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
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
    Garante que tabelas e dados básicos existam.
    """
    bd = BancoDeDados()
    bd.criarBanco()
    
    populador = PopulacaoInicial()
    populador.popular_categorias_padrao()
    
    return True 

def main():
    inicializar_sistema()
    
    app = AppInterface()
    app.run()

if __name__ == "__main__":
    main()