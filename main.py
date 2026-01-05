# Arquivo: Main.py

import streamlit as st
from Persistencia.Banco import BancoDeDados
from UI.App import AppInterface

# CONFIGURAÇÃO: initial_sidebar_state="collapsed" faz o menu começar fechado
st.set_page_config(
    page_title="Gestão Família Enterprise",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed" # <--- MUDANÇA AQUI (Era 'expanded')
)

def inicializar_sistema():
    # ... (Resto do código igual) ...
    bd = BancoDeDados()
    bd.criarBanco()

def main():
    inicializar_sistema()
    app = AppInterface()
    app.executar()

if __name__ == "__main__":
    main()