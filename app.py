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
# ESTILIZAÇÃO CUSTOMIZADA (CSS DARK MODE ESPORTIVO)
# ----------------------------------------------------
st.markdown("""
<style>
    /* Estilização Geral da Aplicação - Slate Dark Elegante de Alto Contraste */
    .stApp {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Cabeçalho do Streamlit (Remover Barra Branca no Topo) */
    header[data-testid="stHeader"], .stAppHeader, header {
        background-color: #0F172A !important;
        background: #0F172A !important;
        color: #F8FAFC !important;
    }
    
    div[data-testid="stToolbar"], div[data-testid="stDecoration"] {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }

    /* Rótulos e Rótulos de Formulários (Labels) - Alto Contraste */
    label, label p, .stWidgetLabel, div[data-testid="stWidgetLabel"] p, .stMarkdown p, span {
        color: #F8FAFC !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }

    /* Rótulos e Texto Principal - Alto Contraste */
    .stMarkdown, .stMarkdown p, label, .stWidgetLabel p, span {
        color: #F8FAFC !important;
    }

    /* Entradas de Texto, Números e Selectbox */
    input, select, textarea, div[data-baseweb="input"] input {
        background-color: #334155 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: 1px solid #475569 !important;
    }

    div[data-baseweb="select"] > div, div[data-baseweb="select"] span, div[data-baseweb="select"] div {
        background-color: #334155 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }

    /* Menu Suspenso do Selectbox (Dropdown Listbox) */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], li[role="option"] {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #334155 !important;
        color: #00E676 !important;
    }

    /* Metric Cards - Destaque Visual */
    div[data-testid="stMetric"] {
        background-color: #0F172A !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.9rem !important;
        font-weight: 800 !important;
        color: #00E676 !important;
    }
    
    div[data-testid="stMetricLabel"] p {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #CBD5E1 !important;
    }

    /* Botões Principais - Neon Verde */
    .stButton > button {
        background: linear-gradient(135deg, #00C853 0%, #00E676 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 28px !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 14px rgba(0, 230, 118, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 230, 118, 0.5) !important;
    }

    /* Sidebar Estilizada de Alto Contraste */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155 !important;
    }

    section[data-testid="stSidebar"] *, section[data-testid="stSidebar"] p {
        color: #F8FAFC !important;
    }

    /* Radios e Checkboxes */
    div[data-testid="stMarkdownContainer"] p {
        color: #F8FAFC !important;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# BARRA LATERAL DE NAVEGAÇÃO E RECURSOS
# ----------------------------------------------------
st.sidebar.title("⚽ Múltiplas Seguras")
st.sidebar.caption("Sistema Avançado de Análise Esportiva")

app_mode = st.sidebar.radio(
    "Navegue pelos Painéis:", 
    [
        "🔍 Analisador de Partidas", 
        "📝 Simulador de Bilhetes", 
        "📈 Projeto de Alavancagem", 
        "🔥 Monitor Mina de Ouro (Ao Vivo)",
        "🌐 Integração Packball"
    ]
)

st.sidebar.markdown("---")
if "api_key" not in st.session_state:
    st.session_state["api_key"] = "5555576d9dcbeed51c0625dcad03a722"

with st.sidebar.expander("⚙️ Configurações da API de Futebol"):
    api_key_input = st.text_input("Chave API-Football (RapidAPI):", value=st.session_state["api_key"], type="password", help="Chave pré-configurada para buscar partidas e dados em tempo real.")
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        st.success("Chave de API ativa!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Status dos Dados Locais")
data = load_data()
st.sidebar.text(f"Partidas Salvas: {len(data.get('matches', []))}")
st.sidebar.text(f"Bilhetes Armazenados: {len(data.get('tickets', []))}")
st.sidebar.text(f"Sinais Ao Vivo: {len(data.get('live_signals', []))}")
st.sidebar.text(f"Etapa Atual: {data.get('leverage_progress', {}).get('current_step', 0)} / 100")

# ----------------------------------------------------
# ROTEAMENTO DOS DASHBOARDS
# ----------------------------------------------------
if app_mode == "🔍 Analisador de Partidas":
    render_match_analyzer()

elif app_mode == "📝 Simulador de Bilhetes":
    render_ticket_simulator()

elif app_mode == "📈 Projeto de Alavancagem":
    render_leverage_project()

elif app_mode == "🔥 Monitor Mina de Ouro (Ao Vivo)":
    render_live_monitor()

elif app_mode == "🌐 Integração Packball":
    render_packball_integration()

# Rodapé profissional
st.markdown("---")
st.caption("⚽ **Método Múltiplas Seguras & Mina de Ouro** | Desenvolvido em Python + Streamlit para Gestão & Engenharia Financeira de Apostas Esportivas.")
