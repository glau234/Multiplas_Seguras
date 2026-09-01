import streamlit as st
import os
import sys

# Adiciona o diretório atual ao sys.path
sys.path.append(os.path.dirname(__file__))

from utils.storage import ensure_data_file, load_data
from views.match_analyzer import render_match_analyzer
from views.ticket_simulator import render_ticket_simulator
from views.leverage_project import render_leverage_project
from views.live_monitor import render_live_monitor
from views.packball_integration import render_packball_integration
from views.gemini_advisor import render_gemini_advisor
from views.paper_trading import render_paper_trading
from views.login_view import render_login_view
from views.admin_management import render_admin_management
from views.predictions import render_predictions
from views.home_view import render_home_view

# ----------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ----------------------------------------------------
st.set_page_config(
    page_title="Método Múltiplas Seguras & Mina de Ouro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Garante que o arquivo JSON local exista
ensure_data_file()

# ----------------------------------------------------
# ESTILIZAÇÃO CUSTOMIZADA (CLEAN MODERN LIGHT AESTHETIC)
# ----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Fundo Geral - Soft Porcelain / Clean Modern */
    .stApp {
        background-color: #F4F6F8 !important;
        color: #111827 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Cabeçalho do Streamlit Integrado e Limpo */
    header[data-testid="stHeader"], .stAppHeader, header {
        background-color: #F4F6F8 !important;
        background: #F4F6F8 !important;
        color: #111827 !important;
    }
    
    div[data-testid="stToolbar"], div[data-testid="stDecoration"] {
        background-color: #F4F6F8 !important;
        color: #111827 !important;
    }

    /* Sidebar Estilo Clean Clay / Neumorphic */
    section[data-testid="stSidebar"] {
        background-color: #FAFAFB !important;
        border-right: 1px solid #E5E7EB !important;
        box-shadow: 2px 0 12px rgba(0, 0, 0, 0.02) !important;
    }

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #111827 !important;
        font-weight: 800 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #374151 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Navegação por Radio na Sidebar */
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        padding: 8px 12px !important;
        margin-bottom: 6px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        display: flex !important;
        align-items: center !important;
    }

    div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        border-color: #93C5FD !important;
        background: #F8FAFC !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stSidebar"] div[role="radiogroup"] > label p {
        color: #1F2937 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
    }

    /* Títulos & Tipografia Principal */
    h1, h2, h3, h4, h5, h6 {
        color: #111827 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }

    p, label {
        color: #374151 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Containers e Cards com Bordas Arredondadas e Sombra Suave */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stVerticalBlockBorderWrapper"]),
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.03), 0 2px 6px -1px rgba(0, 0, 0, 0.02) !important;
    }

    /* Metric Cards Modernos */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 18px !important;
        padding: 16px 18px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06) !important;
    }

    div[data-testid="stMetricValue"], 
    div[data-testid="stMetricValue"] * {
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        color: #111827 !important;
        letter-spacing: -0.03em !important;
    }

    div[data-testid="stMetricLabel"] p {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #6B7280 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.03em !important;
    }

    /* Inputs, Number Inputs, Text Area */
    input, select, textarea, div[data-baseweb="input"] input, div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }

    div[data-baseweb="input"] input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    }

    /* Selectboxes & Dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        font-weight: 600 !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 14px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], li[role="option"] {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
    }

    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #EFF6FF !important;
        color: #2563EB !important;
    }

    /* BOTÕES MODERNOS - 100% LEGÍVEIS COM TEXTO BRANCO PURO */
    .stButton > button,
    div[data-testid="stButton"] > button {
        background: #111827 !important;
        border: 1px solid #111827 !important;
        border-radius: 14px !important;
        padding: 12px 24px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(17, 24, 39, 0.15) !important;
    }

    .stButton > button *,
    .stButton > button p,
    .stButton > button span,
    .stButton > button div,
    div[data-testid="stButton"] > button * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.01em !important;
    }

    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover {
        background: #1F2937 !important;
        border-color: #1F2937 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(17, 24, 39, 0.25) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Barras de Progresso Suaves */
    div[data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #2563EB 0%, #3B82F6 100%) !important;
        border-radius: 999px !important;
    }

    div[data-testid="stProgress"] > div > div {
        background-color: #E5E7EB !important;
        border-radius: 999px !important;
    }

    /* Alertas & Banners de Sucesso/Informação (Design Clean) */
    div[data-testid="stAlert"] {
        border-radius: 16px !important;
        border: 1px solid #E5E7EB !important;
        background: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03) !important;
    }

    div[data-testid="stAlert"] p {
        color: #1F2937 !important;
        font-weight: 600 !important;
    }

    /* EXPANDERS CLEAN MODERN (SEM SOBREPOSIÇÃO DE ÍCONE) */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
        margin-bottom: 12px !important;
    }

    div[data-testid="stExpander"] summary {
        padding: 10px 14px !important;
        border-radius: 16px !important;
    }

    div[data-testid="stExpander"] summary p {
        color: #111827 !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        margin: 0 !important;
    }

    div[data-testid="stExpander"] summary:hover p {
        color: #2563EB !important;
    }

    /* Tabelas e DataFrames Clean */
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02) !important;
        overflow: hidden !important;
    }

    /* Sliders */
    div[data-testid="stSlider"] div[data-baseweb="slider"] {
        color: #2563EB !important;
    }

    div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {
        background-color: #2563EB !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.4) !important;
    }

    /* Modern Tabs / Abas de Ligas */
    div[data-testid="stTabs"] {
        margin-top: 10px !important;
        margin-bottom: 20px !important;
    }

    div[data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: #E5E7EB !important;
        padding: 6px !important;
        border-radius: 16px !important;
        border: 1px solid #D1D5DB !important;
    }

    button[data-baseweb="tab"] {
        border-radius: 12px !important;
        padding: 8px 16px !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #374151 !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    button[data-baseweb="tab"] p {
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        color: #374151 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #111827 !important;
        box-shadow: 0 4px 12px rgba(17, 24, 39, 0.15) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    button[data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background-color: #F3F4F6 !important;
    }

    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Separadores */
    hr {
        border-color: #E5E7EB !important;
        margin: 1.5rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------
# CAMADA DE AUTENTICAÇÃO E SEGURANÇA (LOGIN VIP)
# ----------------------------------------------------
if "authenticated_user" not in st.session_state or not st.session_state.get("authenticated_user"):
    render_login_view()
    st.stop()
else:
    current_user = st.session_state.get("authenticated_user", {})
    is_admin = (current_user.get("role") == "admin")

    # ----------------------------------------------------
    # BARRA LATERAL DE NAVEGAÇÃO E RECURSOS
    with st.sidebar:
        st.markdown("### 👤 Usuário Logado")
        st.markdown(f"**{current_user.get('name', 'Usuário')}**")
        user_role_label = "👑 Administrador VIP" if is_admin else "⚽ Membro VIP"
        st.caption(f"📧 `{current_user.get('email', '')}`\n\nNível: **{user_role_label}**")
        if st.button("🚪 Sair da Conta", use_container_width=True):
            st.session_state["authenticated_user"] = None
            st.rerun()

    menu_options = [
        "🏠 Tela Inicial (Dashboard)",
        "🌐 Integração Packball VIP",
        "🔮 Previsões (Ligas Favoritas)",
        "🎟️ Simulador de Bilhetes", 
        "📈 Simulador Virtual (Paper Trading)"
    ]

    if is_admin:
        menu_options.append("👑 Gestão de Usuários (Admin)")

    if "selected_nav" not in st.session_state or st.session_state["selected_nav"] not in menu_options:
        st.session_state["selected_nav"] = "🏠 Tela Inicial (Dashboard)"

    st.session_state["nav_radio_state"] = st.session_state["selected_nav"]

    def on_nav_change():
        st.session_state["selected_nav"] = st.session_state["nav_radio_state"]

    current_idx = menu_options.index(st.session_state["selected_nav"])

    app_mode = st.sidebar.radio(
        "Navegue pelos Painéis (v2):", 
        options=menu_options,
        index=current_idx,
        key="nav_radio_state",
        on_change=on_nav_change
    )

    st.sidebar.markdown("---")

    # Configurações Gemini AI
    from utils.gemini_assistant import get_api_key
    if "gemini_api_key" not in st.session_state or not st.session_state["gemini_api_key"]:
        st.session_state["gemini_api_key"] = get_api_key() or ""
    
    if st.session_state["gemini_api_key"]:
        os.environ["GEMINI_API_KEY"] = st.session_state["gemini_api_key"]

    with st.sidebar.expander("🤖 Configuração Gemini AI (Google)", expanded=not bool(st.session_state["gemini_api_key"])):
        gemini_key_input = st.text_input(
            "Chave API Gemini:", 
            value=st.session_state["gemini_api_key"], 
            type="password", 
            help="Chave configurada e salva automaticamente."
        )
        if gemini_key_input:
            st.session_state["gemini_api_key"] = gemini_key_input
            os.environ["GEMINI_API_KEY"] = gemini_key_input
            st.success("IA Gemini Conectada e Ativa!")
        else:
            st.caption("Obtenha sua chave em [Google AI Studio](https://aistudio.google.com/).")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Status dos Dados no Banco")
    
    from utils.supabase_db import is_supabase_configured
    if is_supabase_configured():
        st.sidebar.success("🟢 Supabase (Nuvem Ativa)")
    else:
        st.sidebar.caption("📁 Banco de Dados Local (JSON)")

    data = load_data()
    total_bilhetes = len(data.get('tickets', []))
    total_simulacoes = len(data.get('simulated_tickets', []))

    st.sidebar.text(f"🎫 Bilhetes no Banco: {total_bilhetes}")
    st.sidebar.text(f"📈 Simulações Virtuais: {total_simulacoes}")

    # ----------------------------------------------------
    # ROTEAMENTO DOS DASHBOARDS (VERSÃO 2)
    # ----------------------------------------------------
    if app_mode == "🏠 Tela Inicial (Dashboard)":
        render_home_view(is_admin)

    elif app_mode == "🌐 Integração Packball VIP":
        render_packball_integration()

    elif app_mode == "🔮 Previsões (Ligas Favoritas)":
        render_predictions()

    elif app_mode == "🎟️ Simulador de Bilhetes":
        render_ticket_simulator()

    elif app_mode == "📈 Simulador Virtual (Paper Trading)":
        render_paper_trading()

    elif app_mode == "👑 Gestão de Usuários (Admin)":
        render_admin_management()

# Rodapé profissional
st.markdown("---")
st.caption("⚽ **Método Múltiplas Seguras & Mina de Ouro** | Desenvolvido em Python + Streamlit para Gestão & Engenharia Financeira de Apostas Esportivas.")
