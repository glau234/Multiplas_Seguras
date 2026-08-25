import streamlit as st
import time
from utils.packball_scraper import fetch_packball_matches
from utils.calculations import (
    calculate_xg_and_defense, 
    calculate_team_corners, 
    filter_out_serie_b, 
    group_matches_by_league,
    get_country_flag
)

def render_packball_integration():
    # Se houver um jogo selecionado para visualização completa em página dedicada
    selected_match = st.session_state.get("selected_packball_match", None)
    if selected_match:
        render_match_details_page(selected_match)
        return

    st.title("🌐 Integração Packball VIP - Estatísticas Oficiais")
    st.markdown("Extração oficial dos próximos 7 dias do Packball para assinantes VIP com **separação automática por ligas** e exclusão obrigatória da Série B brasileira. Dados nativos de **ExG (Gols)**, **ExC (Escanteios)**, **Ambas Marcam (BTS %)**, **PPG** e **Poder Defensivo**.")

    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔑 Credenciais Packball VIP")
        username = st.text_input("Usuário / Email:", placeholder="seu_email@exemplo.com", value="glaucio.silveira@gmail.com")
        password = st.text_input("Senha:", type="password", value="Denise23")
        
        num_dias = st.number_input("📅 Quantidade de Dias para Extração:", min_value=1, max_value=14, value=3, step=1, help="Escolha quantos dias futuros (a partir de hoje) você deseja varrer e extrair do Packball.")
        
        st.markdown("#### 🎯 Filtros Estatísticos (Packball Nativo)")
        filtro_max_exg = st.slider("ExG Máximo da Partida (Packball):", min_value=1.50, max_value=4.50, value=3.20, step=0.1, help="Partidas com menor ExG favorecem o Handicap +3 e mercados Under.")
        filtro_max_diff = st.slider("Diferença Máxima de Odds (Equilíbrio):", min_value=0.50, max_value=3.50, value=2.50, step=0.1, help="Garante que as partidas sejam parelhas e equilibradas.")
        
        st.info("🛡️ **Critério Ativo de Segurança:** Partidas da **Série B do Campeonato Brasileiro** são excluídas automaticamente da extração.")
        
        if st.button(f"🚀 Iniciar Extração Oficial VIP ({num_dias} Dias)", use_container_width=True):
            if not username or not password:
                st.error("Por favor, insira o usuário e a senha do Packball.")
            else:
                with st.spinner(f"Conectando à sua conta VIP do Packball e extraindo métricas oficiais dos próximos {num_dias} dias..."):
                    raw_matches = fetch_packball_matches(username, password, num_days=num_dias)
                    
                    if raw_matches and isinstance(raw_matches, dict) and "error" in raw_matches:
                        st.error(raw_matches.get("error", "Erro desconhecido ao extrair dados."))
                    elif raw_matches:
                        # 1. Filtrar partidas da Série B do Brasileirão
                        clean_matches = filter_out_serie_b(raw_matches)
                        
                        # 2. Enriquecer com métricas de defesa calculadas sobre os dados reais
                        enriched_matches = []
                        for m in clean_matches:
                            stats = calculate_xg_and_defense(m.get("odd_casa", 2.0), m.get("odd_empate", 3.10), m.get("odd_visi", 2.0))
                            enriched_match = dict(m)
                            enriched_match.update(stats)
                            if "exg" in m and m["exg"]:
                                enriched_match["exg_oficial"] = m["exg"]
                            else:
                                enriched_match["exg_oficial"] = stats["xg_total"]
                            enriched_matches.append(enriched_match)
                            
                        st.session_state["packball_matches"] = enriched_matches
                        st.success(f"✅ {len(enriched_matches)} partidas VIP extraídas e organizadas por ligas!")
                    else:
                        st.warning("Nenhum jogo encontrado que atenda aos critérios.")

    with col2:
        st.subheader("📊 Painel de Confrontos por Ligas")
        
        if "packball_matches" in st.session_state:
            raw_stored_matches = st.session_state["packball_matches"]
            matches = filter_out_serie_b(raw_stored_matches)
            
            if not matches:
                st.info("Nenhuma partida encontrada após a aplicação dos filtros.")
            else:
                # Agrupar partidas por liga
                grouped_by_league = group_matches_by_league(matches)
                total_ligas = len(grouped_by_league)
                
                # Calcular aprovados gerais
                todos_aprovados = []
                for m in matches:
                    odd_c = m.get("odd_casa", 1.0)
                    odd_v = m.get("odd_visi", 1.0)
                    exg_val = float(m.get("exg_oficial", m.get("exg", 2.5)))
                    diff_odd = abs(odd_c - odd_v)
                    if (diff_odd <= filtro_max_diff) and (exg_val <= filtro_max_exg):
                        todos_aprovados.append(m)
                
                # Métricas do topo
                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("Total de Ligas", f"{total_ligas}")
                c_m2.metric("Total de Jogos", f"{len(matches)}")
                c_m3.metric("Jogos Aprovados", f"{len(todos_aprovados)}", delta="Qualificados" if todos_aprovados else "0")
                
                st.markdown("---")
                st.markdown("### 🗂️ Selecione a Aba da Liga Desejada:")
                
                # Criação das Abas Reais por Liga
                tab_titles = [f"🌐 Todas as Ligas ({len(matches)})"] + [
                    f"{league_name} ({len(l_matches)})" for league_name, l_matches in grouped_by_league.items()
                ]
                tabs = st.tabs(tab_titles)
                
                # Aba 0: Visão Geral de Todas as Ligas
                with tabs[0]:
                    if len(todos_aprovados) > 0:
                        if st.button(f"➕ Enviar Todos os {len(todos_aprovados)} Jogos Aprovados de Todas as Ligas para o Simulador", key="btn_send_all_global", use_container_width=True):
                            transformed_aprovados = []
                            for m in todos_aprovados:
                                maior_odd_time = m['time_casa'] if m.get('odd_casa', 1.0) > m.get('odd_visi', 1.0) else m['time_visi']
                                transformed_aprovados.append({
                                    "id": m.get("id", str(time.time())),
                                    "jogo": f"{m['time_casa']} vs {m['time_visi']}",
                                    "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                                    "odd": 1.15,
                                    "status": "Pendente",
                                    "data": m.get("data", "Hoje"),
                                    "liga": m.get("liga", "")
                                })
                            st.session_state["packball_approved_matches"] = transformed_aprovados
                            st.success(f"✅ {len(todos_aprovados)} partidas de todas as ligas enviadas para o Simulador!")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    for lg_idx, (league_title, league_matches) in enumerate(grouped_by_league.items()):
                        with st.container(border=True):
                            render_league_section(league_title, league_matches, filtro_max_diff, filtro_max_exg, tab_key=f"all_{lg_idx}", show_header=True)
                
                # Abas 1..N: Abas Individuais de cada Liga (ex: Serie A do Brasil, La Liga, etc.)
                for i, (league_title, league_matches) in enumerate(grouped_by_league.items(), start=1):
                    with tabs[i]:
                        render_league_section(league_title, league_matches, filtro_max_diff, filtro_max_exg, tab_key=f"tab_single_{i}", show_header=True)
        else:
            st.info("Preencha suas credenciais VIP e inicie a extração para visualizar todos os dados nativos do Packball organizados por abas de ligas.")


def render_match_card(match, idx, tab_key, filtro_max_diff, filtro_max_exg):
    """Renderiza o card visual de uma partida individual."""
    odd_casa = match.get("odd_casa", 2.0)
    odd_empate = match.get("odd_empate", 3.10)
    odd_visi = match.get("odd_visi", 2.0)
    exg_oficial = match.get("exg_oficial", match.get("exg", 2.5))
    escanteios_avg = match.get("escanteios_avg", match.get("corners", "N/A"))
    escanteios_exc = match.get("escanteios_exc", "")
    
    # Calcular ExC do Jogo e por Time
    exc_base = escanteios_exc if escanteios_exc else escanteios_avg
    corners_calc = calculate_team_corners(exc_base, odd_casa, odd_visi)
    
    pais = match.get("pais", "")
    liga = match.get("liga", "")
    data_str = match.get("data", "Hoje")
    horario = match.get("horario", "--:--")
    
    diff_odd = abs(odd_casa - odd_visi)
    is_match_aprovado = (diff_odd <= filtro_max_diff) and (float(exg_oficial) <= filtro_max_exg)
    status_icon = "🟢" if is_match_aprovado else "⚪"
    status_badge = "Aprovado" if is_match_aprovado else "Fora dos Filtros"
    
    with st.container(border=True):
        c_match_info, c_match_btn = st.columns([3, 1.2])
        with c_match_info:
            st.markdown(f"#### {status_icon} {match['time_casa']} vs {match['time_visi']}")
            st.caption(f"📅 **{data_str}** | ⏰ **{horario}** | 🏆 **{liga}** ({pais}) | 💰 **Odds:** {odd_casa:.2f} x {odd_empate:.2f} x {odd_visi:.2f} (Diff: {diff_odd:.2f})")
            st.markdown(f"⚽ **ExG Oficial:** `{exg_oficial}` | 🚩 **ExC Jogo:** `{corners_calc['exc_total']}` (Casa: `{corners_calc['exc_casa']}` | Visi: `{corners_calc['exc_visi']}`) | 🎯 **Status:** `{status_badge}`")
        with c_match_btn:
            st.write("")
            if st.button("🔍 Ver Diagnóstico", key=f"btn_detalhe_{tab_key}_{idx}_{match.get('id', idx)}", use_container_width=True):
                st.session_state["selected_packball_match"] = match
                st.rerun()
            
            # Botão para adicionar jogo individual
            if st.button("➕ Add Bilhete", key=f"btn_add_card_{tab_key}_{idx}_{match.get('id', idx)}", use_container_width=True):
                if "packball_approved_matches" not in st.session_state:
                    st.session_state["packball_approved_matches"] = []
                maior_odd_time = match['time_casa'] if odd_casa > odd_visi else match['time_visi']
                st.session_state["packball_approved_matches"].append({
                    "id": match.get("id", str(time.time())),
                    "jogo": f"{match['time_casa']} vs {match['time_visi']}",
                    "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                    "odd": 1.15,
                    "status": "Pendente",
                    "data": match.get("data", "Hoje"),
                    "liga": match.get("liga", "")
                })
                st.toast(f"Adicionado: {match['time_casa']} vs {match['time_visi']}", icon="✅")


def render_league_section(league_title, league_matches, filtro_max_diff, filtro_max_exg, tab_key, show_header=True):
    """Renderiza o cabeçalho e todas as partidas de uma liga."""
    aprovados_liga = [
        m for m in league_matches 
        if (abs(m.get("odd_casa", 1.0) - m.get("odd_visi", 1.0)) <= filtro_max_diff) and 
           (float(m.get("exg_oficial", m.get("exg", 2.5))) <= filtro_max_exg)
    ]
    
    if show_header:
        c_lg_title, c_lg_action = st.columns([2.5, 1.5])
        with c_lg_title:
            st.markdown(f"### {league_title}")
            st.caption(f"📊 **{len(league_matches)} confronto(s)** nesta liga &nbsp;|&nbsp; 🟢 **{len(aprovados_liga)} aprovado(s)** pelos critérios")
        with c_lg_action:
            if len(aprovados_liga) > 0:
                if st.button(f"➕ Enviar Aprovados ({len(aprovados_liga)})", key=f"btn_send_lg_{tab_key}_{league_title}", use_container_width=True):
                    if "packball_approved_matches" not in st.session_state:
                        st.session_state["packball_approved_matches"] = []
                    
                    for m in aprovados_liga:
                        maior_odd_time = m['time_casa'] if m.get('odd_casa', 1.0) > m.get('odd_visi', 1.0) else m['time_visi']
                        st.session_state["packball_approved_matches"].append({
                            "id": m.get("id", str(time.time())),
                            "jogo": f"{m['time_casa']} vs {m['time_visi']}",
                            "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                            "odd": 1.15,
                            "status": "Pendente",
                            "data": m.get("data", "Hoje"),
                            "liga": m.get("liga", "")
                        })
                    st.success(f"✅ {len(aprovados_liga)} jogo(s) de {league_title} enviados para o Simulador!")
        st.markdown("---")

    for idx, match in enumerate(league_matches):
        render_match_card(match, idx, tab_key, filtro_max_diff, filtro_max_exg)




def render_match_details_page(match):
    """
    Renderiza uma página dedicada e ampla com todos os dados e diagnósticos detalhados da partida.
    """
    col_nav1, col_nav2 = st.columns([1, 4])
    with col_nav1:
        if st.button("⬅️ Voltar para Lista de Jogos", use_container_width=True):
            st.session_state["selected_packball_match"] = None
            st.rerun()
            
    with col_nav2:
        st.caption("Visão Expandida & Diagnóstico Detalhado do Packball VIP")
        
    st.markdown("---")
    
    # Dados da partida
    odd_casa = match.get("odd_casa", 2.0)
    odd_empate = match.get("odd_empate", 3.10)
    odd_visi = match.get("odd_visi", 2.0)
    exg_oficial = match.get("exg_oficial", match.get("exg", 2.5))
    gols_avg = match.get("gols_avg", "N/A")
    over25 = match.get("over25", "N/A")
    bts = match.get("bts", "N/A")
    win_prob = match.get("win_prob", "N/A")
    ppg = match.get("ppg", "N/A")
    escanteios_avg = match.get("escanteios_avg", match.get("corners", "N/A"))
    escanteios_exc = match.get("escanteios_exc", "")
    
    # Cálculo das expectativas de escanteios (Jogo + Cada Equipe)
    exc_base = escanteios_exc if escanteios_exc else escanteios_avg
    corners_calc = calculate_team_corners(exc_base, odd_casa, odd_visi)
    
    pais = match.get("pais", "")
    liga = match.get("liga", "")
    horario = match.get("horario", "")
    data_str = match.get("data", "Hoje")
    
    def_casa = match.get("poder_def_casa", 65)
    def_visi = match.get("poder_def_visi", 65)
    cs_casa = match.get("clean_sheet_casa", 40.0)
    cs_visi = match.get("clean_sheet_visi", 40.0)
    
    maior_odd_time = match['time_casa'] if odd_casa > odd_visi else match['time_visi']
    
    # Header Principal
    st.markdown(f"# ⚔️ {match['time_casa']} vs {match['time_visi']}")
    st.markdown(f"📅 **Data:** {data_str} &nbsp;|&nbsp; ⏰ **Horário:** {horario} &nbsp;|&nbsp; 🏆 **Liga:** {liga} ({pais}) &nbsp;|&nbsp; ⭐ **Critério FAV:** *Sem favorito ou leve favoritismo*")
    
    st.markdown("---")
    
    # Bloco 1: Cotações e Mercado Recomendado
    st.subheader("💰 Cotações 1X2 & Mercado Múltiplas Seguras")
    col_c1, col_c2, col_c3, col_c4 = st.columns([1, 1, 1, 1.5])
    
    col_c1.metric(f"Vitória {match['time_casa']}", f"{odd_casa:.2f}", help="Odd para vitória do time mandante.")
    col_c2.metric("Empate", f"{odd_empate:.2f}", help="Odd para empate.")
    col_c3.metric(f"Vitória {match['time_visi']}", f"{odd_visi:.2f}", help="Odd para vitória do time visitante.")
    
    with col_c4:
        st.success(f"🛡️ **Entrada Sugerida:**\n**Handicap Europeu +3 ({maior_odd_time})**\nOdd Estimada: ~1.12 - 1.18")
        
    st.markdown("---")
    
    # Bloco 2: Expectativa e Distribuição de Escanteios (ExC)
    st.subheader("🚩 Análise Detalhada de Escanteios (ExC & AVG)")
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    
    with col_e1:
        st.metric("🎯 ExC Total do Jogo", f"{corners_calc['exc_total']} cantos", help="Expectativa total de escanteios projetada para a partida.")
        st.caption(f"Média Histórica (AVG): **{escanteios_avg}**")
        
    with col_e2:
        st.metric(f"🏠 ExC {match['time_casa']}", f"{corners_calc['exc_casa']} cantos", help=f"Expectativa de escanteios para o {match['time_casa']}.")
        st.caption(f"Domínio Ofensivo: **{corners_calc['share_casa_pct']}%**")
        
    with col_e3:
        st.metric(f"✈️ ExC {match['time_visi']}", f"{corners_calc['exc_visi']} cantos", help=f"Expectativa de escanteios para o {match['time_visi']}.")
        st.caption(f"Domínio Ofensivo: **{corners_calc['share_visi_pct']}%**")
        
    with col_e4:
        st.metric("📊 Média das Equipes (AVG)", f"{escanteios_avg} cantos", help="Média combinada de escanteios das equipes por jogo.")
        st.caption("Packball Nativo")
        
    # Barra de distribuição de escanteios
    st.caption(f"Proporção de Escanteios Esperados: **{match['time_casa']} ({corners_calc['exc_casa']})** vs **{match['time_visi']} ({corners_calc['exc_visi']})**")
    st.progress(corners_calc['share_casa_pct'] / 100.0)
    
    st.markdown("---")
    
    # Bloco 3: Estatísticas Oficiais de Gols do Packball VIP
    st.subheader("📈 Estatísticas Nativas e Oficiais do Packball VIP")
    
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("🎯 Expectativa de Gols (ExG)", f"{exg_oficial} gols", help="Média esperada de gols calculada pelos modelos matemáticos do Packball.")
        st.caption(f"Média Histórica de Gols (AVG): **{gols_avg}**")
        
    with col_s2:
        st.metric("⚽ Ambas Marcam (BTS %)", f"{bts}", help="Probabilidade percentual de ambas as equipes marcarem gols.")
        st.caption(f"Prob. Over 2.5 Gols: **{over25 if over25 else 'N/A'}**")
        
    with col_s3:
        st.metric("🏆 Prob. Vitória (% Win)", f"{win_prob}", help="Probabilidade estimada de vitória Casa vs Visitante.")
        st.caption("Projeção Packball")
        
    with col_s4:
        st.metric("📈 Pontos Por Jogo (PPG)", f"{ppg}", help="Média de pontos por jogo no campeonato.")
        st.caption(f"Horário: **{horario}**")

    st.markdown("---")
    
    # Bloco 4: Análise Tática e Poder Defensivo
    st.subheader("🛡️ Diagnóstico de Solidez Defensiva & Clean Sheet")
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown(f"#### Defesa {match['time_casa']}")
        st.progress(min(def_casa / 100.0, 1.0))
        st.write(f"🛡️ **Solidez Defensiva:** **{def_casa}%**")
        st.write(f"🧤 **Probabilidade de Não Sofrer Gol (Clean Sheet):** **{cs_casa}%**")
        
    with col_d2:
        st.markdown(f"#### Defesa {match['time_visi']}")
        st.progress(min(def_visi / 100.0, 1.0))
        st.write(f"🛡️ **Solidez Defensiva:** **{def_visi}%**")
        st.write(f"🧤 **Probabilidade de Não Sofrer Gol (Clean Sheet):** **{cs_visi}%**")
        
    st.markdown("---")
    
    st.markdown("---")

    # Bloco 5: Diagnóstico com Google Gemini AI
    st.subheader("🤖 Diagnóstico Especialista com Google Gemini")
    gemini_key = st.session_state.get("gemini_api_key", "")
    
    if not gemini_key:
        st.info("💡 Insira sua Chave da API do Gemini na barra lateral para liberar análises com inteligência artificial sobre esta partida.")
    else:
        from utils.gemini_assistant import analyze_match_with_gemini
        
        pergunta_custom = st.text_input("Deseja fazer alguma pergunta específica sobre este confronto ao Gemini?", placeholder="Ex: O Handicap +3 é seguro considerando a média de gols dos últimos 5 jogos?", key="input_ia_match")
        
        if st.button("✨ Gerar Parecer Tático com IA", use_container_width=True, key="btn_ia_match_analyze"):
            with st.spinner("O Google Gemini está analisando as estatísticas, cotações e poder defensivo deste jogo..."):
                parecer = analyze_match_with_gemini(match, gemini_key, pergunta_custom)
                st.session_state[f"ia_parecer_{match.get('id')}"] = parecer
                
        if f"ia_parecer_{match.get('id')}" in st.session_state:
            with st.container(border=True):
                st.markdown("### 🧠 Parecer da Inteligência Artificial:")
                st.markdown(st.session_state[f"ia_parecer_{match.get('id')}"])

    st.markdown("---")
    
    # Bloco 6: Ações
    st.subheader("⚡ Ações para este Jogo")
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button("➕ Adicionar Jogo ao Simulador de Bilhetes", key="btn_add_single", use_container_width=True):
            if "packball_approved_matches" not in st.session_state:
                st.session_state["packball_approved_matches"] = []
                
            st.session_state["packball_approved_matches"].append({
                "id": match.get("id", str(time.time())),
                "jogo": f"{match['time_casa']} vs {match['time_visi']}",
                "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                "odd": 1.15,
                "status": "Pendente",
                "data": match.get("data", "Hoje"),
                "liga": match.get("liga", "")
            })
            st.success(f"✅ Partida **{match['time_casa']} vs {match['time_visi']}** adicionada ao Simulador de Bilhetes!")
            
    with btn_col2:
        if st.button("⬅️ Voltar para Todos os Confrontos", key="btn_back_bottom", use_container_width=True):
            st.session_state["selected_packball_match"] = None
            st.rerun()


