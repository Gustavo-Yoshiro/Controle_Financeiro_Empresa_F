import streamlit as st
from streamlit_option_menu import option_menu

# Imports dos Services
from Service import ConfiguracaoService, FinanceiroService, CategoriaService, RelatorioFinanceiroService
from Service import InquilinoService, KitnetService, LocacaoService, RelatorioKitnetService
from Service import FrotaService, EmpresaService, LogisticaService, RelatorioFrotaService
from Service import PixService, BoletoService, EmprestimoService, CreditoService 

# Imports das Pages
from UI.Pages import DashboardPage, FinanceiroPage, DividasPage, KitnetsPage, VeiculosPage, PixPage, ConfiguracoesPage

# --- 🔒 CONFIGURAÇÃO DE SEGURANÇA ---
try:
    SENHA_DO_SISTEMA = st.secrets["senha_sistema"]
except FileNotFoundError:
    st.error("Arquivo .streamlit/secrets.toml não encontrado!")
    st.stop()
except KeyError:
    st.error("A chave 'senha_sistema' não foi definida nos segredos!")
    st.stop()

class AppInterface:
    def __init__(self):
        # 1. Instancia Serviços Básicos
        self.s_config = ConfiguracaoService()
        self.s_categoria = CategoriaService()
        self.s_inquilino = InquilinoService()
        self.s_kitnet = KitnetService()
        self.s_empresa = EmpresaService()

        # 2. Financeiro Core
        self.s_financeiro = FinanceiroService() 
        self.s_relatorio_fin = RelatorioFinanceiroService(self.s_categoria)

        # 3. Regras de Negócio
        self.s_locacao = LocacaoService(self.s_financeiro)
        self.s_logistica = LogisticaService(self.s_financeiro)
        self.s_frota = FrotaService(self.s_financeiro)
        
        # 4. Relatórios
        self.s_relatorio_kit = RelatorioKitnetService()
        self.s_relatorio_frota = RelatorioFrotaService()

        # 5. Outros (Bancários e Dívidas)
        self.s_pix = PixService()
        self.s_boleto = BoletoService(self.s_financeiro)
        self.s_emprestimo = EmprestimoService(self.s_financeiro)
        
        # --- NOVO SERVIÇO DE CRÉDITO ---
        # Ele precisa do financeiro para lançar os pagamentos de fatura
        self.s_credito = CreditoService(self.s_financeiro)

        # Configura CSS Global
        self._configurar_estilo()

        # 6. Instancia as Páginas
        self.pages = {
            "Dashboard": DashboardPage(self.s_relatorio_fin, self.s_relatorio_frota, self.s_config),
            "Lançamentos": FinanceiroPage(self.s_financeiro, self.s_categoria, self.s_relatorio_fin, self.s_config),
            
            # --- ATUALIZADO AQUI ---
            # Passando o s_credito para a página de dívidas
            "Dívidas & Boletos": DividasPage(self.s_boleto, self.s_emprestimo, self.s_config, self.s_credito),
            # -----------------------

            "Kitnets & Aluguéis": KitnetsPage(
                self.s_inquilino, self.s_kitnet, self.s_locacao, 
                self.s_relatorio_kit, self.s_financeiro, self.s_config
            ),
            "Frota & Logística": VeiculosPage(
                self.s_frota, self.s_empresa, self.s_logistica, 
                self.s_relatorio_frota, self.s_config, self.s_boleto
            ),
            "Gerenciador Pix": PixPage(self.s_pix, self.s_config),
            "Configurações": ConfiguracoesPage(
                self.s_config, self.s_kitnet, self.s_inquilino, self.s_financeiro, 
                self.s_frota, self.s_pix, self.s_boleto, self.s_emprestimo
            )
        }

    def _configurar_estilo(self):
        st.markdown("""
        <style>
            .block-container { padding-top: 1rem; padding-bottom: 3rem; }
            div[data-testid="stMetric"] {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
            }
        </style>
        """, unsafe_allow_html=True)

    def _renderizar_login(self):
        """ Renderiza a tela de bloqueio se não estiver logado """
        st.markdown("<br><br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.container(border=True):
                st.title("🔒 Acesso Restrito")
                st.markdown("Sistema de Gestão Família Enterprise")
                
                senha = st.text_input("Senha de Acesso", type="password")
                
                if st.button("Entrar", type="primary", width='stretch'):
                    if senha == SENHA_DO_SISTEMA:
                        st.session_state["logado"] = True
                        st.toast("Acesso Liberado!")
                        st.rerun()
                    else:
                        st.error("Senha Incorreta")

    def run(self):
        # 1. VERIFICAÇÃO DE SESSÃO
        if "logado" not in st.session_state:
            st.session_state["logado"] = False

        # 2. DECISÃO: LOGIN OU SISTEMA
        if not st.session_state["logado"]:
            self._renderizar_login()
        else:
            # --- SISTEMA COMPLETO ---
            with st.sidebar:
                st.title("Gestão Integrada")
                
                selected = option_menu(
                    menu_title="Menu Principal",
                    options=list(self.pages.keys()),
                    icons=["graph-up", "currency-dollar", "receipt", "house", "truck", "qr-code", "gear"], 
                    menu_icon="cast",
                    default_index=0,
                )
                
                st.markdown("---")
                # Botão de Logout
                if st.button("🔓 Sair / Logout", width='stretch'):
                    st.session_state["logado"] = False
                    st.rerun()

                st.caption("Sistema v6.1 - Família Enterprise")
            
            # Renderiza a página escolhida
            if selected in self.pages:
                self.pages[selected].render()