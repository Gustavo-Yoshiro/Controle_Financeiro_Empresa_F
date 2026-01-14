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
    initial_sidebar_state="collapsed" # Começa fechado para focar no Login
)

@st.cache_resource
def inicializar_sistema():
    """
    Roda apenas uma vez quando o servidor sobe.
    Garante que tabelas e dados básicos existam.
    """
    # 1. Cria tabelas
    bd = BancoDeDados()
    bd.criarBanco()
    
    # 2. Popula dados padrão (Bancos, Categorias, Formas Pgto)
    populador = PopulacaoInicial()
    populador.popular_tudo()
    
    return True 

def main():
    # Garante que o banco existe antes de carregar a Interface
    inicializar_sistema()
    
    # Inicia a Interface (que tem a lógica de Login dentro dela)
    app = AppInterface()
    app.run()

if __name__ == "__main__":
    main()