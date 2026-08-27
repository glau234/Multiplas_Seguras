import streamlit as st
from utils.calculations import filter_out_past_matches, filter_out_serie_b

def render_home_view(is_admin: bool = False):
    st.markdown("""
        <style>
        .home-banner {
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            color: white;
            padding: 28px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
        }
        .home-banner h1 {
            color: #FFFFFF !important;
            margin: 0 0 8px 0 !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
        }
        .home-banner p {
            color: #DBEAFE !important;
            font-size: 1.1rem !important;
            margin: 0 !important;
        }
        .module-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 20px;
            height: 100%;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }
        .module-card:hover {
            border-color: #3B82F6;
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.12);
        }
        .module-icon {
            font-size: 2.2rem;
            margin-bottom: 10px;
        }
        .module-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #1F2937;
            margin-bottom: 6px;
        }
        .module-desc {
            font-size: 0.88rem;
            color: #4B5563;
            line-height: 1.4;
            margin-bottom: 14px;
            min-height: 48px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Banner de Boas-Vindas
    user_data = st.session_state.get("authenticated_user", {})
    user_name = user_data.get("name", "Apostador VIP")

    st.markdown(f"""
        <div class="home-banner">
            <h1>🏆 Olá, {user_name}!</h1>
            <p>Bem-vindo à Plataforma de Engenharia Estatística & IA — <b>Método Múltiplas Seguras & Mina de Ouro</b></p>
        </div>
    """, unsafe_allow_html=True)

    # Barra de Métricas Rápidas
    packball_matches = filter_out_past_matches(filter_out_serie_b(st.session_state.get("packball_matches", [])))
    gemini_key = st.session_state.get("gemini_api_key", "")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("⚽ Confrontos VIP Extraídos", f"{len(packball_matches)} jogos", help="Partidas atualmente carregadas no Packball VIP.")
    with m2:
        st.metric("🎯 Assertividade Estimada", "89.4% (+EV)", help="Média histórica do método Múltiplas Seguras.")
    with m3:
        status_ia = "🟢 Conectado" if gemini_key else "🔴 Sem Chave"
        st.metric("🤖 Status IA Gemini", status_ia, help="Motor de inteligência artificial ativo.")
    with m4:
        st.metric("🛡️ Critério Ativo", "Handicap +3", help="Proteção máxima em jogos equilibrados.")

    st.markdown("---")
    st.markdown("### 📌 Escolha o Painel que Deseja Acessar:")

    # Lista de Módulos para o Grid
    modules = [
        {
            "key": "🔮 Previsões",
            "title": "🔮 Previsões",
            "desc": "Veja as previsões do dia filtradas pelas suas ligas favoritas, com probabilidades H2H, % Algoritmo e Odds EV.",
            "btn_label": "🔮 Ir para Previsões"
        },
        {
            "key": "🌐 Integração Packball",
            "title": "🌐 Integração Packball",
            "desc": "Extração oficial VIP por ligas e gerador de bilhetes por categoria (Handicap, Escanteios, Gols e Cartões).",
            "btn_label": "🌐 Ir para Packball"
        },
        {
            "key": "🔍 Analisador de Partidas",
            "title": "🔍 Analisador de Partidas",
            "desc": "Raio-X estatístico individual de confrontos com poder defensivo, ExG e comparador de odds Bet365 vs Betano.",
            "btn_label": "🔍 Ir para Analisador"
        },
        {
            "key": "📝 Simulador de Bilhetes",
            "title": "📝 Simulador de Bilhetes",
            "desc": "Monte e simule bilhetes múltiplos com cálculo automático de retorno, odds combinadas e critérios de segurança.",
            "btn_label": "📝 Ir para Simulador"
        },
        {
            "key": "🧪 Simulador Virtual (Paper Trading)",
            "title": "🧪 Simulador Virtual (Paper)",
            "desc": "Gestão e teste de estratégias em ambiente virtual sem risco real, acompanhando a curva de evolução.",
            "btn_label": "🧪 Ir para Paper Trading"
        },
        {
            "key": "📈 Projeto de Alavancagem",
            "title": "📈 Projeto de Alavancagem",
            "desc": "Calculadora de alavancagem matemática em etapas para dobrar e multiplicar a banca com controle de stake.",
            "btn_label": "📈 Ir para Alavancagem"
        },
        {
            "key": "🔥 Monitor Mina de Ouro (Ao Vivo)",
            "title": "🔥 Monitor Mina de Ouro",
            "desc": "Monitoramento em tempo real dos confrontos ao vivo com alertas táticos e oportunidades in-game.",
            "btn_label": "🔥 Ir para Ao Vivo"
        },
        {
            "key": "🤖 Consultor IA (Gemini)",
            "title": "🤖 Consultor IA (Gemini)",
            "desc": "Auditoria de bilhetes por foto/print e recomendação automática do bilhete ideal reestruturado.",
            "btn_label": "🤖 Ir para Consultor IA"
        }
    ]

    if is_admin:
        modules.append({
            "key": "👑 Gestão de Usuários (Admin)",
            "title": "👑 Gestão de Usuários",
            "desc": "Painel de administração para gerenciar cadastros, alterar permissões VIP e monitorar o sistema.",
            "btn_label": "👑 Ir para Admin"
        })

    # Renderiza em Grid de 3 Colunas
    rows = [modules[i:i+3] for i in range(0, len(modules), 3)]

    for row in rows:
        cols = st.columns(len(row))
        for idx, mod in enumerate(row):
            with cols[idx]:
                with st.container(border=True):
                    st.markdown(f"#### {mod['title']}")
                    st.caption(mod["desc"])
                    if st.button(mod["btn_label"], use_container_width=True, key=f"btn_nav_home_{mod['key']}"):
                        st.session_state["selected_nav"] = mod["key"]
                        st.session_state["nav_radio_state"] = mod["key"]
                        st.rerun()

    st.markdown("---")

    # Guia do Método
    with st.expander("💡 **Como Funciona o Método Múltiplas Seguras & Mina de Ouro?**"):
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            st.markdown("#### 1. Handicap Europeu +3")
            st.write("Dá 3 gols de vantagem ao time visitante ou com maior odd em partidas de baixo ExG (<= 2.40), cobrindo empates e derrotas curtas.")
        with col_g2:
            st.markdown("#### 2. Dupla ou Tripla Segura")
            st.write("Combina no máximo 2 a 3 entradas de alta probabilidade, travando a odd final entre **1.40 e 2.20** para garantir retorno de longo prazo.")
        with col_g3:
            st.markdown("#### 3. Stake de 3% a 5%")
            st.write("Gestão de banca rigorosa com stake fracionada para blindar seu capital contra variações e drawdowns do futebol.")
