import streamlit as st
import sys
from config.settings import PAGE_TITLE, PAGE_ICON
from views.dashboard import render_dashboard_view
from views.injetoras import render_injetoras_view
from views.moldes import render_moldes_view
from views.ordens import render_ordens_view
from views.apontamentos import render_apontamento_view
from database.schema import criar_banco, verificar_atualizacoes

# Forçar UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuração da página
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuração de tema e estilo
st.markdown("""
    <style>
        @media (max-width: 640px) {
            .stTextInput input, .stNumberInput input, .stDateInput input {
                font-size: 16px;
                min-height: 40px;
            }
            .stSelectbox select {
                font-size: 16px;
                min-height: 40px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Criar/atualizar banco de dados
if not criar_banco():
    st.error("Erro ao criar banco de dados!")
    st.stop()

if not verificar_atualizacoes():
    st.warning("Algumas atualizações do banco de dados podem não ter sido aplicadas.")

# Menu de navegação
st.sidebar.title("📱 Menu")
pagina = st.sidebar.radio(
    "Ir para:",
    ["Dashboard", "Cadastro de Injetoras", "Cadastro de Moldes", 
     "Ordem de Produção", "Apontamento de Produção"]
)

# Renderizar a página selecionada
if pagina == "Dashboard":
    render_dashboard_view()
elif pagina == "Cadastro de Injetoras":
    render_injetoras_view()
elif pagina == "Cadastro de Moldes":
    render_moldes_view()
elif pagina == "Ordem de Produção":
    render_ordens_view()
else:  # Apontamento de Produção
    render_apontamento_view()