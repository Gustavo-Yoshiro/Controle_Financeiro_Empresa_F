import streamlit as st
from streamlit_option_menu import option_menu


from Service import ConfiguracaoService, FinanceiroService, CategoriaService, RelatorioFinanceiroService

from Service import InquilinoService, KitnetService, LocacaoService, RelatorioKitnetService

from Service import FrotaService, EmpresaService, LogisticaService, RelatorioFrotaService

from Service import PixService, BoletoService, EmprestimoService


from UI.Pages import DashboardPage, FinanceiroPage, DividasPage, KitnetsPage, VeiculosPage, PixPage, ConfiguracoesPage

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

        # 3. Regras de Negócio (Injetando Financeiro)
        self.s_locacao = LocacaoService(self.s_financeiro)
        self.s_logistica = LogisticaService(self.s_financeiro)
        self.s_frota = FrotaService(self.s_financeiro)
        
        # 4. Serviços de Leitura (Relatórios)
        self.s_relatorio_kit = RelatorioKitnetService()
        self.s_relatorio_frota = RelatorioFrotaService()

        # 5. Outros
        self.s_pix = PixService()
        self.s_boleto = BoletoService(self.s_financeiro)
        self.s_emprestimo = EmprestimoService(self.s_financeiro)

        # Configura CSS Global
        self._configurar_estilo()

        # 6. Instancia as Páginas (Injeção de Dependência)
        self.pages = {
            "Dashboard": DashboardPage(self.s_relatorio_fin, self.s_relatorio_frota, self.s_config),
            
            "Lançamentos": FinanceiroPage(self.s_financeiro, self.s_categoria, self.s_relatorio_fin, self.s_config),
            
            "Dívidas & Boletos": DividasPage(self.s_boleto, self.s_emprestimo, self.s_config),
            
            "Kitnets & Aluguéis": KitnetsPage(
                self.s_inquilino, self.s_kitnet, self.s_locacao, 
                self.s_relatorio_kit, self.s_financeiro, self.s_config
            ),
            
            "Frota & Logística": VeiculosPage(
                self.s_frota, self.s_empresa, self.s_logistica, 
                self.s_relatorio_frota, self.s_config
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

    def run(self):
        with st.sidebar:
            st.title("Gestão Integrada")
            
            selected = option_menu(
                menu_title="Menu Principal",
                options=list(self.pages.keys()),
                icons=[
                    "graph-up",       # Dashboard
                    "currency-dollar", # Lançamentos
                    "receipt",        # Dívidas
                    "house",          # Kitnets
                    "truck",          # Frota
                    "qr-code",        # Pix
                    "gear"            # Config
                ], 
                menu_icon="cast",
                default_index=0,
            )
            
            st.markdown("---")
            st.caption("Sistema v2.0 - Família Enterprise")
        
        # Renderiza a página escolhida
        if selected in self.pages:
            self.pages[selected].render()