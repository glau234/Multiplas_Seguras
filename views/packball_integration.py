import streamlit as st
import time
import os
import json
from utils.packball_scraper import fetch_packball_matches
from utils.calculations import (
    calculate_xg_and_defense, 
    calculate_team_corners, 
    filter_out_serie_b, 
    filter_out_past_matches,
    group_matches_by_league,
    get_country_flag,
    sort_matches_by_datetime,
    filter_matches_by_datetime
)
from utils.gemini_assistant import (
    lookup_or_generate_match_packball_stats,
    analyze_match_best_ticket,
    generate_categorized_packball_tickets,
    get_api_key
)
from utils.odds_comparator import render_bookmaker_comparison_card

def render_packball_integration():
    # Auto-carregamento do cache caso ainda não exista na sessão (filtrando jogos passados)
    if "packball_matches" not in st.session_state:
        if os.path.exists("data/cached_packball.json"):
            try:
                with open("data/cached_packball.json", "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    if cached and len(cached) > 0:
                        st.session_state["packball_matches"] = filter_out_past_matches(cached)
            except Exception:
                pass

    # Se houver um jogo selecionado para visualização completa em página dedicada
    selected_match = st.session_state.get("selected_packball_match", None)
    if selected_match:
        render_match_details_page(selected_match)
        return

    st.title("🌐 Integração Packball VIP - Estatísticas Oficiais")
    st.markdown("Extração oficial dos próximos dias do Packball para assinantes VIP com **separação automática por ligas**, exclusão da Série B e **gerador de bilhetes por categorias (Handicap, Escanteios, Gols e Cartões)**.")

    st.markdown("---")

    tab_extraction, tab_search, tab_categorized = st.tabs([
        "🌐 Extração Oficial VIP por Ligas", 
        "🔍 Consulta de Qualquer Jogo (Packball + IA)",
        "🎟️ Criar Bilhetes por Categoria (Handicap, Escanteios, Gols, Cartões)"
    ])

    gemini_key = st.session_state.get("gemini_api_key") or get_api_key()

    # ====================================================
    # ABA 1: EXTRAÇÃO OFICIAL VIP POR LIGAS
    # ====================================================
    with tab_extraction:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🔑 Credenciais Packball VIP")
            username = st.text_input("Usuário / Email:", placeholder="seu_email@exemplo.com", value="glaucio.silveira@gmail.com")
            password = st.text_input("Senha:", type="password", value="Denise23")
            
            num_dias = st.number_input("📅 Quantidade de Dias para Extração:", min_value=1, max_value=14, value=3, step=1, help="Escolha quantos dias futuros você deseja varrer e extrair do Packball.")
            
            st.markdown("#### 🎯 Filtros Estatísticos (Packball Nativo)")
            filtro_max_exg = st.slider("ExG Máximo da Partida (Packball):", min_value=1.50, max_value=4.50, value=3.20, step=0.1, help="Partidas com menor ExG favorecem o Handicap +3 e mercados Under.")
            filtro_max_diff = st.slider("Diferença Máxima de Odds (Equilíbrio):", min_value=0.50, max_value=3.50, value=2.50, step=0.1, help="Garante que as partidas sejam parelhas e equilibradas.")

            st.info("🛡️ **Critério Ativo de Segurança:** Partidas da **Série B do Campeonato Brasileiro** e partidas com **datas anteriores a hoje** são excluídas automaticamente da extração.")
            
            if st.button(f"🚀 Iniciar Extração Oficial VIP ({num_dias} Dias)", use_container_width=True):
                if not username or not password:
                    st.error("Por favor, insira o usuário e a senha do Packball.")
                else:
                    with st.spinner(f"Conectando à sua conta VIP do Packball e extraindo métricas oficiais dos próximos {num_dias} dias..."):
                        raw_matches = fetch_packball_matches(username, password, num_days=num_dias)
                        
                        if raw_matches and isinstance(raw_matches, dict) and "error" in raw_matches:
                            st.error(raw_matches.get("error", "Erro desconhecido ao extrair dados."))
                        elif raw_matches:
                            clean_matches = filter_out_past_matches(filter_out_serie_b(raw_matches))
                            
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
                matches = filter_out_past_matches(filter_out_serie_b(raw_stored_matches))
                
                # ====================================================
                # FILTROS DE DATA, HORA E ORDENAÇÃO (DIRETO NO PAINEL)
                # ====================================================
                available_dates = ["Todas as Datas"]
                raw_dates = [str(m.get("data", "")).strip() for m in matches if m.get("data")]
                unique_dates = list(dict.fromkeys(raw_dates))
                available_dates.extend(unique_dates)

                with st.expander("📅 ⏰ **Filtros por Data, Horário & Ordenação Cronológica**", expanded=True):
                    f_col1, f_col2, f_col3 = st.columns([1.5, 2, 1.2])
                    with f_col1:
                        filtro_data_selecionada = st.selectbox(
                            "📅 Filtrar por Data:",
                            options=available_dates,
                            index=0,
                            key="p_filter_date"
                        )
                    with f_col2:
                        filtro_hora_range = st.slider(
                            "⏰ Intervalo de Horário:",
                            min_value=0,
                            max_value=23,
                            value=(0, 23),
                            format="%d:00 h",
                            key="p_filter_time"
                        )
                    with f_col3:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        ordem_crescente = st.checkbox(
                            "⬆️ Ordem Crescente",
                            value=True,
                            key="p_order_asc",
                            help="Organiza todas as partidas do jogo mais cedo ao jogo mais tardio de forma cronológica crescente."
                        )

                # Aplica o filtro de Data e Hora
                matches = filter_matches_by_datetime(
                    matches,
                    selected_date=filtro_data_selecionada,
                    hora_inicio=filtro_hora_range[0],
                    hora_fim=filtro_hora_range[1]
                )
                
                # Aplica a ordenação por Data e Hora de forma crescente (se ativada)
                matches = sort_matches_by_datetime(matches, ascending=ordem_crescente)
                
                if not matches:
                    st.info("💡 Nenhuma partida encontrada para a data e horário selecionados.")
                else:
                    grouped_by_league = group_matches_by_league(matches)
                    
                    league_names = ["Todas as Partidas Extraídas (" + str(len(matches)) + ")"]
                    league_names.extend([f"{league} ({len(l_matches)})" for league, l_matches in grouped_by_league.items()])
                    
                    tabs = st.tabs(league_names)
                    
                    with tabs[0]:
                        col_top_act1, col_top_act2 = st.columns([2, 1])
                        with col_top_act1:
                            st.caption(f"Exibindo todas as **{len(matches)} partidas** organizadas em ordem cronológica.")
                        with col_top_act2:
                            if st.button("➕ Enviar Todas para Simulador", use_container_width=True, key="btn_send_all_sim"):
                                if "packball_approved_matches" not in st.session_state:
                                    st.session_state["packball_approved_matches"] = []
                                
                                transformed_aprovados = []
                                for m in matches:
                                    odd_c = float(m.get("odd_casa", 2.0))
                                    odd_v = float(m.get("odd_visi", 2.0))
                                    maior_odd_time = m["time_casa"] if odd_c > odd_v else m["time_visi"]
                                    
                                    data_str = m.get("data", "")
                                    horario_str = m.get("horario", "")
                                    dh_str = f"{data_str} {horario_str}".strip() if horario_str and horario_str not in data_str else data_str
                                    
                                    transformed_aprovados.append({
                                        "id": m.get("id", str(time.time())),
                                        "jogo": f"{m['time_casa']} vs {m['time_visi']}",
                                        "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                                        "odd": 1.15,
                                        "status": "Pendente",
                                        "data": dh_str,
                                        "horario": horario_str,
                                        "liga": m.get("liga", "")
                                    })
                                
                                st.session_state["packball_approved_matches"].extend(transformed_aprovados)
                                st.success(f"✅ {len(transformed_aprovados)} partidas enviadas para o Simulador de Bilhetes!")
                        
                        render_league_section("Todas as Partidas Extraídas", matches, filtro_max_diff, filtro_max_exg, "todas", show_header=False)
                    
                    for idx_tab, (league_name, league_matches) in enumerate(grouped_by_league.items(), start=1):
                        with tabs[idx_tab]:
                            render_league_section(league_name, league_matches, filtro_max_diff, filtro_max_exg, f"tab_{idx_tab}")

            else:
                st.info("👈 Insira suas credenciais VIP ao lado e clique em **Iniciar Extração** para carregar os confrontos organizados por ligas.")

    # ====================================================
    # ABA 2: CONSULTA DIRETA DE QUALQUER JOGO + MELHOR BILHETE IA
    # ====================================================
    with tab_search:
        render_match_query_module()

    # ====================================================
    # ABA 3: CRIAR BILHETES POR CATEGORIA (HANDICAP, ESCANTEIOS, GOLS, CARTÕES)
    # ====================================================
    with tab_categorized:
        st.subheader("🎟️ Gerador de Bilhetes Ideais por Categoria (Handicap, Escanteios, Gols & Cartões)")
        st.markdown(
            "Faça o **upload de uma foto/print**, **descreva os jogos em texto** ou **selecione partidas do Packball VIP**. "
            "O algoritmo e o Google Gemini montarão automaticamente os **melhores bilhetes estratégicos** divididos pelas 4 categorias de mercado: "
            "**Handicap Europeu +3**, **Escanteios**, **Gols/Ambos Marcam** e **Cartões**, além da **Múltipla Master**."
        )

        col_cat1, col_cat2 = st.columns([1.2, 1])
        with col_cat1:
            st.markdown("#### 1. Upload de Imagem ou Print do Bilhete")
            cat_file = st.file_uploader(
                "Envie uma foto ou print com as partidas:",
                type=["png", "jpg", "jpeg", "webp", "pdf", "txt"],
                key="cat_ticket_uploader"
            )
            if cat_file:
                if cat_file.type.startswith("image/"):
                    st.image(cat_file, caption="📸 Imagem Anexada", use_container_width=True)
                else:
                    st.info(f"📄 Arquivo: {cat_file.name}")

        with col_cat2:
            st.markdown("#### 2. Descrever Jogos ou Selecionar do Packball")
            cat_text = st.text_area(
                "Cole ou descreva as partidas desejadas:",
                placeholder="Exemplo:\n1. Real Madrid vs Osasuna\n2. Flamengo vs Botafogo\n3. Manchester City vs Everton",
                height=120,
                key="cat_ticket_text_area"
            )

            stored_matches = filter_out_serie_b(st.session_state.get("packball_matches", []))
            packball_options = [f"{m['time_casa']} vs {m['time_visi']} ({m.get('liga', '')})" for m in stored_matches]
            selected_matches_labels = st.multiselect(
                "Ou selecione entre os jogos extraídos do Packball VIP:",
                options=packball_options,
                key="cat_ticket_multiselect"
            )

        st.markdown("---")
        if st.button("🚀 Gerar Melhores Bilhetes (Handicap, Escanteios, Gols & Cartões)", type="primary", use_container_width=True, key="btn_generate_categorized_tickets"):
            games_payload_parts = []
            if cat_text.strip():
                games_payload_parts.append(cat_text.strip())
            if selected_matches_labels:
                games_payload_parts.append("Jogos Selecionados do Packball:\n" + "\n".join(selected_matches_labels))

            final_games_text = "\n\n".join(games_payload_parts)

            if not cat_file and not final_games_text.strip():
                st.error("⚠️ Por favor, envie uma foto, digite jogos em texto OU selecione ao menos 1 partida do Packball.")
            else:
                with st.spinner("🤖 O Google Gemini está analisando os confrontos e compilando os 5 melhores bilhetes estratégicos por categoria..."):
                    img_b = cat_file.getvalue() if cat_file and cat_file.type.startswith("image/") else None
                    
                    res_categorized = generate_categorized_packball_tickets(
                        games_text=final_games_text,
                        image_bytes=img_b,
                        api_key=gemini_key,
                        cached_matches=stored_matches
                    )

                    st.session_state["packball_categorized_result"] = res_categorized
                    st.rerun()

        # Exibição do Resultado por Categorias
        if st.session_state.get("packball_categorized_result"):
            st.markdown("---")
            with st.container(border=True):
                st.markdown("## 🧠 Painel de Bilhetes por Categoria (Método Múltiplas Seguras)")
                st.markdown(st.session_state["packball_categorized_result"])

                st.markdown("---")
                col_cadd1, col_cadd2 = st.columns(2)
                with col_cadd1:
                    if st.button("➕ Enviar Bilhetes Gerados para o Simulador", type="primary", use_container_width=True, key="btn_send_cat_sim"):
                        if "packball_approved_matches" not in st.session_state:
                            st.session_state["packball_approved_matches"] = []

                        st.session_state["packball_approved_matches"].append({
                            "id": f"cat_{time.time()}",
                            "jogo": "Combo por Categorias (Packball + IA)",
                            "mercado": "Handicap +3, Escanteios, Gols e Cartões",
                            "odd": 1.90,
                            "status": "Pendente",
                            "data": "Hoje",
                            "horario": "Vários",
                            "liga": "Múltiplas Seguras"
                        })
                        st.toast("✅ Bilhetes por categoria enviados para o Simulador!", icon="🎟️")
                with col_cadd2:
                    if st.button("🧹 Limpar Bilhetes Categorizados", use_container_width=True, key="btn_clear_cat_sim"):
                        st.session_state["packball_categorized_result"] = None
                        st.rerun()

    # ====================================================
    # ABA 1: EXTRAÇÃO OFICIAL VIP POR LIGAS
    # ====================================================
    with tab_extraction:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🔑 Credenciais Packball VIP")
            username = st.text_input("Usuário / Email:", placeholder="seu_email@exemplo.com", value="glaucio.silveira@gmail.com")
            password = st.text_input("Senha:", type="password", value="Denise23")
            
            num_dias = st.number_input("📅 Quantidade de Dias para Extração:", min_value=1, max_value=14, value=3, step=1, help="Escolha quantos dias futuros você deseja varrer e extrair do Packball.")
            
            st.markdown("#### 🎯 Filtros Estatísticos (Packball Nativo)")
            filtro_max_exg = st.slider("ExG Máximo da Partida (Packball):", min_value=1.50, max_value=4.50, value=3.20, step=0.1, help="Partidas com menor ExG favorecem o Handicap +3 e mercados Under.")
            filtro_max_diff = st.slider("Diferença Máxima de Odds (Equilíbrio):", min_value=0.50, max_value=3.50, value=2.50, step=0.1, help="Garante que as partidas sejam parelhas e equilibradas.")

            st.info("🛡️ **Critério Ativo de Segurança:** Partidas da **Série B do Campeonato Brasileiro** e partidas com **datas anteriores a hoje** são excluídas automaticamente da extração.")
            
            if st.button(f"🚀 Iniciar Extração Oficial VIP ({num_dias} Dias)", use_container_width=True):
                if not username or not password:
                    st.error("Por favor, insira o usuário e a senha do Packball.")
                else:
                    with st.spinner(f"Conectando à sua conta VIP do Packball e extraindo métricas oficiais dos próximos {num_dias} dias..."):
                        raw_matches = fetch_packball_matches(username, password, num_days=num_dias)
                        
                        if raw_matches and isinstance(raw_matches, dict) and "error" in raw_matches:
                            st.error(raw_matches.get("error", "Erro desconhecido ao extrair dados."))
                        elif raw_matches:
                            clean_matches = filter_out_past_matches(filter_out_serie_b(raw_matches))
                            
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
                matches = filter_out_past_matches(filter_out_serie_b(raw_stored_matches))
                
                # ====================================================
                # FILTROS DE DATA, HORA E ORDENAÇÃO (DIRETO NO PAINEL)
                # ====================================================
                available_dates = ["Todas as Datas"]
                raw_dates = [str(m.get("data", "")).strip() for m in matches if m.get("data")]
                unique_dates = list(dict.fromkeys(raw_dates))
                available_dates.extend(unique_dates)

                with st.expander("📅 ⏰ **Filtros por Data, Horário & Ordenação Cronológica**", expanded=True):
                    f_col1, f_col2, f_col3 = st.columns([1.5, 2, 1.2])
                    with f_col1:
                        filtro_data_selecionada = st.selectbox(
                            "📅 Filtrar por Data:",
                            options=available_dates,
                            index=0,
                            key="p_filter_date"
                        )
                    with f_col2:
                        filtro_hora_range = st.slider(
                            "⏰ Intervalo de Horário:",
                            min_value=0,
                            max_value=23,
                            value=(0, 23),
                            format="%d:00 h",
                            key="p_filter_time"
                        )
                    with f_col3:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        ordem_crescente = st.checkbox(
                            "⬆️ Ordem Crescente",
                            value=True,
                            key="p_order_asc",
                            help="Organiza todas as partidas do jogo mais cedo ao jogo mais tardio de forma cronológica crescente."
                        )

                # Aplica o filtro de Data e Hora
                matches = filter_matches_by_datetime(
                    matches,
                    selected_date=filtro_data_selecionada,
                    hora_inicio=filtro_hora_range[0],
                    hora_fim=filtro_hora_range[1]
                )
                
                # Aplica a ordenação por Data e Hora de forma crescente (se ativada)
                matches = sort_matches_by_datetime(matches, ascending=ordem_crescente)
                
                if not matches:
                    st.info("Nenhuma partida encontrada após a aplicação dos filtros.")
                else:
                    grouped_by_league = group_matches_by_league(matches)
                    total_ligas = len(grouped_by_league)
                    
                    todos_aprovados = []
                    for m in matches:
                        odd_c = m.get("odd_casa", 1.0)
                        odd_v = m.get("odd_visi", 1.0)
                        exg_val = float(m.get("exg_oficial", m.get("exg", 2.5)))
                        diff_odd = abs(odd_c - odd_v)
                        if (diff_odd <= filtro_max_diff) and (exg_val <= filtro_max_exg):
                            todos_aprovados.append(m)
                    
                    c_m1, c_m2, c_m3 = st.columns(3)
                    c_m1.metric("Total de Ligas", f"{total_ligas}")
                    c_m2.metric("Total de Jogos", f"{len(matches)}")
                    c_m3.metric("Jogos Aprovados", f"{len(todos_aprovados)}", delta="Qualificados" if todos_aprovados else "0")
                    
                    st.markdown("---")
                    st.markdown("### 🗂️ Selecione a Aba da Liga Desejada:")
                    
                    tab_titles = [f"🌐 Todas as Ligas ({len(matches)})"] + [
                        f"{league_name} ({len(l_matches)})" for league_name, l_matches in grouped_by_league.items()
                    ]
                    tabs = st.tabs(tab_titles)
                    
                    with tabs[0]:
                        if len(todos_aprovados) > 0:
                            if st.button(f"➕ Enviar Todos os {len(todos_aprovados)} Jogos Aprovados de Todas as Ligas para o Simulador", key="btn_send_all_global", use_container_width=True):
                                transformed_aprovados = []
                                for m in todos_aprovados:
                                    maior_odd_time = m['time_casa'] if m.get('odd_casa', 1.0) > m.get('odd_visi', 1.0) else m['time_visi']
                                    d_str = m.get("data", "Hoje")
                                    h_str = m.get("horario", "")
                                    dh_str = f"{d_str} {h_str}".strip() if h_str and h_str not in d_str else d_str
                                    transformed_aprovados.append({
                                        "id": m.get("id", str(time.time())),
                                        "jogo": f"{m['time_casa']} vs {m['time_visi']}",
                                        "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                                        "odd": 1.15,
                                        "status": "Pendente",
                                        "data": dh_str,
                                        "horario": h_str,
                                        "liga": m.get("liga", "")
                                    })
                                if "packball_approved_matches" not in st.session_state:
                                    st.session_state["packball_approved_matches"] = []
                                st.session_state["packball_approved_matches"].extend(transformed_aprovados)
                                st.success(f"✅ {len(transformed_aprovados)} partidas enviadas para o Simulador de Bilhetes!")
                        
                        render_league_section("Todas as Partidas Extraídas", matches, filtro_max_diff, filtro_max_exg, "todas", show_header=False)
                    
                    for idx_tab, (league_name, league_matches) in enumerate(grouped_by_league.items(), start=1):
                        with tabs[idx_tab]:
                            render_league_section(league_name, league_matches, filtro_max_diff, filtro_max_exg, f"tab_{idx_tab}")

            else:
                st.info("👈 Insira suas credenciais VIP ao lado e clique em **Iniciar Extração** para carregar os confrontos organizados por ligas.")

    # ====================================================
    # ABA 2: CONSULTA DIRETA DE QUALQUER JOGO + MELHOR BILHETE IA
    # ====================================================
    with tab_search:
        render_match_query_module()


def render_match_query_module():
    """
    Permite consultar estatísticas completas do Packball VIP para QUALQUER jogo
    (mesmo não filtrado) e pedir ao Gemini a recomendação do melhor bilhete.
    """
    st.subheader("🔍 Consulta Estatística Packball VIP & Gerador de Bilhete IA")
    st.markdown(
        "Pesquise sobre **qualquer jogo do futebol mundial** (ex: *Flamengo x Botafogo*, *Real Madrid x Barcelona*, *Palmeiras x Corinthians*). "
        "O sistema compilará **todas as métricas oficiais do Packball** (ExG, ExC, BTS, Poder Defensivo, PPG) e o **Google Gemini** indicará a melhor entrada e combinação de bilhete."
    )

    from utils.gemini_assistant import get_api_key
    gemini_key = st.session_state.get("gemini_api_key") or get_api_key()
    cached_matches = st.session_state.get("packball_matches", [])

    # Barra de busca e sugestões
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        query_input = st.text_input(
            "Digite os times ou o confronto que deseja consultar:",
            value=st.session_state.get("last_searched_query", ""),
            placeholder="Ex: Flamengo x Botafogo, Real Madrid vs Real Betis, Palmeiras...",
            key="input_query_match"
        )
    with col_s2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        btn_search = st.button("🔎 Buscar Raio-X", type="primary", use_container_width=True)

    # Exemplos Rápidos de Consulta
    st.caption("⚡ Exemplos rápidos para consultar:")
    col_ex1, col_ex2, col_ex3 = st.columns(3)
    if col_ex1.button("📌 Flamengo x Botafogo", use_container_width=True):
        query_input = "Flamengo x Botafogo"
        btn_search = True
    if col_ex2.button("📌 Real Madrid x Real Betis", use_container_width=True):
        query_input = "Real Madrid x Real Betis"
        btn_search = True
    if col_ex3.button("📌 Palmeiras x São Paulo", use_container_width=True):
        query_input = "Palmeiras x São Paulo"
        btn_search = True

    if btn_search and query_input.strip():
        st.session_state["last_searched_query"] = query_input
        with st.spinner(f"Compilando estatísticas do Packball VIP para '{query_input}'..."):
            match_result = lookup_or_generate_match_packball_stats(query_input, gemini_key, cached_matches)
            st.session_state["queried_packball_match_data"] = match_result
            st.session_state["queried_ai_ticket_result"] = None

    # Exibição dos Dados do Confronto Consultado
    queried_match = st.session_state.get("queried_packball_match_data", None)
    if queried_match:
        st.markdown("---")
        
        # Cabeçalho do Confronto
        t_casa = queried_match.get("time_casa", "Time Casa")
        t_visi = queried_match.get("time_visi", "Time Visitante")
        liga = queried_match.get("liga", "Liga")
        pais = queried_match.get("pais", "")
        horario = queried_match.get("horario", "16:00")
        source = queried_match.get("source", "Packball VIP")
        
        flag = get_country_flag(pais)
        st.markdown(f"## {flag} {t_casa} vs {t_visi}")
        st.caption(f"🏆 **Liga:** {liga} ({pais}) &nbsp;|&nbsp; ⏰ **Horário:** {horario} &nbsp;|&nbsp; 📡 **Origem dos Dados:** {source}")

        # Bloco 1: Cotações 1X2 e Mercado Sugerido
        odd_c = float(queried_match.get("odd_casa", 2.0))
        odd_e = float(queried_match.get("odd_empate", 3.10))
        odd_v = float(queried_match.get("odd_visi", 2.0))
        maior_odd_time = t_casa if odd_c > odd_v else t_visi

        col_c1, col_c2, col_c3, col_c4 = st.columns([1, 1, 1, 1.5])
        col_c1.metric(f"Vitória {t_casa}", f"{odd_c:.2f}")
        col_c2.metric("Empate", f"{odd_e:.2f}")
        col_c3.metric(f"Vitória {t_visi}", f"{odd_v:.2f}")
        with col_c4:
            st.success(f"🛡️ **Entrada Principal:**\n**Handicap Europeu +3 ({maior_odd_time})**\nOdd Estimada: ~1.14 - 1.18")

        # Comparador Bet365 vs Betano
        render_bookmaker_comparison_card(queried_match, market_type="Handicap Europeu +3", compact=False)

        st.markdown("---")

        # Bloco 2: Métricas Nativas de Gols e Escanteios (Packball VIP)
        st.markdown("### 📊 Raio-X Estatístico Completo (Packball VIP)")
        
        exg = queried_match.get("exg_oficial", queried_match.get("exg", 2.3))
        gols_avg = queried_match.get("gols_avg", "2.5")
        bts = queried_match.get("bts", "52%")
        over25 = queried_match.get("over25", "45%")
        win_prob = queried_match.get("win_prob", "50% - 25%")
        ppg = queried_match.get("ppg", "1.8 - 1.5")
        
        exc_avg = float(queried_match.get("escanteios_avg", 9.5))
        exc_calc = calculate_team_corners(exc_avg, odd_c, odd_v)

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("⚽ Expectativa de Gols (ExG)", f"{exg} gols", help="Média projetada de gols do confronto.")
            st.caption(f"Média Histórica: **{gols_avg} gols/jogo**")
        with col_m2:
            st.metric("🚩 Expectativa Escanteios (ExC)", f"{exc_calc['exc_total']} cantos", help="Projeção total de escanteios.")
            st.caption(f"Casa: **{exc_calc['exc_casa']}** | Visitante: **{exc_calc['exc_visi']}**")
        with col_m3:
            st.metric("🥅 Ambas Marcam (BTS %)", f"{bts}", help="Probabilidade de ambos os times marcarem.")
            st.caption(f"Prob. Over 2.5: **{over25}**")
        with col_m4:
            st.metric("🏆 Prob. Vitória (% Win)", f"{win_prob}", help="Projeção percentual de vitória do Packball.")
            st.caption(f"PPG: **{ppg}**")

        # Bloco 3: Poder Defensivo e Clean Sheet
        def_c = int(queried_match.get("poder_def_casa", 70))
        def_v = int(queried_match.get("poder_def_visi", 65))
        cs_c = int(queried_match.get("clean_sheet_casa", 40))
        cs_v = int(queried_match.get("clean_sheet_visi", 35))

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"#### 🛡️ Defesa {t_casa}")
            st.progress(min(def_c / 100.0, 1.0))
            st.write(f"Solidez Defensiva: **{def_c}%** &nbsp;|&nbsp; Clean Sheet: **{cs_c}%**")
        with col_d2:
            st.markdown(f"#### 🛡️ Defesa {t_visi}")
            st.progress(min(def_v / 100.0, 1.0))
            st.write(f"Solidez Defensiva: **{def_v}%** &nbsp;|&nbsp; Clean Sheet: **{cs_v}%**")

        st.markdown("---")

        # Bloco 4: SOLICITAÇÃO AO GEMINI IA - MELHOR BILHETE
        st.subheader("🤖 Consultar Gemini IA: Melhor Bilhete & Análise de Valor")
        st.markdown("Clique abaixo para que a inteligência artificial analise todas essas estatísticas e recomende o melhor bilhete individual e combinado.")

        col_btn_ai1, col_btn_ai2 = st.columns([1.5, 1])
        with col_btn_ai1:
            if st.button("✨ Solicitar ao Gemini IA o Melhor Bilhete para este Jogo", type="primary", use_container_width=True):
                with st.spinner("O Google Gemini está cruzando as métricas do Packball e calculando a melhor estratégia de aposta..."):
                    parecer_ticket = analyze_match_best_ticket(queried_match, gemini_key)
                    st.session_state["queried_ai_ticket_result"] = parecer_ticket

        with col_btn_ai2:
            if st.button("➕ Adicionar Jogo ao Simulador de Bilhetes", use_container_width=True):
                if "packball_approved_matches" not in st.session_state:
                    st.session_state["packball_approved_matches"] = []
                d_str = queried_match.get("data", "Hoje")
                h_str = queried_match.get("horario", "")
                dh_str = f"{d_str} {h_str}".strip() if h_str and h_str not in d_str else d_str
                st.session_state["packball_approved_matches"].append({
                    "id": queried_match.get("id", str(time.time())),
                    "jogo": f"{t_casa} vs {t_visi}",
                    "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                    "odd": 1.15,
                    "status": "Pendente",
                    "data": dh_str,
                    "horario": h_str,
                    "liga": liga
                })
                st.success(f"✅ Partida **{t_casa} vs {t_visi}** adicionada ao Simulador de Bilhetes!")

        # Exibição do Parecer do Gemini IA
        if st.session_state.get("queried_ai_ticket_result"):
            st.markdown("---")
            with st.container(border=True):
                st.markdown("### 🧠 Recomendação de Bilhete & Estratégia do Gemini IA:")
                st.markdown(st.session_state["queried_ai_ticket_result"])


def render_match_card(match, idx, tab_key, filtro_max_diff, filtro_max_exg):
    """Renderiza o card visual premium de um confronto."""
    odd_c = match.get("odd_casa", 1.0)
    odd_v = match.get("odd_visi", 1.0)
    odd_e = match.get("odd_empate", 1.0)
    exg_val = float(match.get("exg_oficial", match.get("exg", 2.5)))
    diff_odd = abs(odd_c - odd_v)
    
    aprovado = (diff_odd <= filtro_max_diff) and (exg_val <= filtro_max_exg)
    
    card_bg = "#FFFFFF"
    card_border = "#E5E7EB"
    status_badge = "🟢 Qualificado" if aprovado else "⚪ Monitoramento"
    
    with st.container(border=True):
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.markdown(f"#### ⚽ {match['time_casa']} vs {match['time_visi']}")
            data_str = match.get("data", "")
            horario_str = match.get("horario", "")
            data_hora_text = f"📅 {data_str} &nbsp;|&nbsp; ⏰ {horario_str}" if data_str else f"⏰ {horario_str}"
            st.caption(f"🏆 {match.get('liga', '')} ({match.get('pais', '')}) &nbsp;|&nbsp; {data_hora_text}")
        with col_header2:
            st.markdown(f"<div style='text-align: right; font-weight: 700;'>{status_badge}</div>", unsafe_allow_html=True)
            
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Vitória {match['time_casa']}", f"{odd_c:.2f}")
        c2.metric("Empate", f"{odd_e:.2f}")
        c3.metric(f"Vitória {match['time_visi']}", f"{odd_v:.2f}")
        c4.metric("ExG Oficial", f"{exg_val} gols")
        
        # Comparativo Compacto Bet365 vs Betano
        render_bookmaker_comparison_card(match, market_type="Handicap Europeu +3", compact=True)
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🔍 Ver Diagnóstico Completo", key=f"diag_{tab_key}_{idx}_{match.get('id', idx)}", use_container_width=True):
                st.session_state["selected_packball_match"] = match
                st.rerun()
        with col_act2:
            if st.button("➕ Adicionar ao Bilhete", key=f"add_{tab_key}_{idx}_{match.get('id', idx)}", use_container_width=True):
                if "packball_approved_matches" not in st.session_state:
                    st.session_state["packball_approved_matches"] = []
                maior_odd_time = match['time_casa'] if odd_c > odd_v else match['time_visi']
                d_str = match.get("data", "Hoje")
                h_str = match.get("horario", "")
                dh_str = f"{d_str} {h_str}".strip() if h_str and h_str not in d_str else d_str
                st.session_state["packball_approved_matches"].append({
                    "id": match.get("id", str(time.time())),
                    "jogo": f"{match['time_casa']} vs {match['time_visi']}",
                    "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                    "odd": 1.15,
                    "status": "Pendente",
                    "data": dh_str,
                    "horario": h_str,
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
                        d_str = m.get("data", "Hoje")
                        h_str = m.get("horario", "")
                        dh_str = f"{d_str} {h_str}".strip() if h_str and h_str not in d_str else d_str
                        st.session_state["packball_approved_matches"].append({
                            "id": m.get("id", str(time.time())),
                            "jogo": f"{m['time_casa']} vs {m['time_visi']}",
                            "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                            "odd": 1.15,
                            "status": "Pendente",
                            "data": dh_str,
                            "horario": h_str,
                            "liga": m.get("liga", "")
                        })
                    st.success(f"✅ {len(aprovados_liga)} jogo(s) de {league_title} enviados para o Simulador!")
        st.markdown("---")

    for idx, match in enumerate(league_matches):
        render_match_card(match, idx, tab_key, filtro_max_diff, filtro_max_exg)


def render_match_details_page(match):
    """Renderiza uma página dedicada com todos os dados do Packball VIP e parecer IA."""
    col_nav1, col_nav2 = st.columns([1, 4])
    with col_nav1:
        if st.button("⬅️ Voltar para Lista de Jogos", use_container_width=True):
            st.session_state["selected_packball_match"] = None
            st.rerun()
            
    with col_nav2:
        st.caption("Visão Expandida & Diagnóstico Detalhado do Packball VIP")
        
    st.markdown("---")
    
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
    
    st.markdown(f"# ⚔️ {match['time_casa']} vs {match['time_visi']}")
    st.markdown(f"📅 **Data:** {data_str} &nbsp;|&nbsp; ⏰ **Horário:** {horario} &nbsp;|&nbsp; 🏆 **Liga:** {liga} ({pais})")
    
    st.markdown("---")
    
    st.subheader("💰 Cotações 1X2 & Mercado Múltiplas Seguras")
    col_c1, col_c2, col_c3, col_c4 = st.columns([1, 1, 1, 1.5])
    col_c1.metric(f"Vitória {match['time_casa']}", f"{odd_casa:.2f}")
    col_c2.metric("Empate", f"{odd_empate:.2f}")
    col_c3.metric(f"Vitória {match['time_visi']}", f"{odd_visi:.2f}")
    with col_c4:
        st.success(f"🛡️ **Entrada Sugerida:**\n**Handicap Europeu +3 ({maior_odd_time})**\nOdd Estimada: ~1.12 - 1.18")
        
    # Comparador Bet365 vs Betano na página de detalhes
    render_bookmaker_comparison_card(match, market_type="Handicap Europeu +3", compact=False)
        
    st.markdown("---")
    
    st.subheader("🚩 Análise Detalhada de Escanteios (ExC & AVG)")
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    with col_e1:
        st.metric("🎯 ExC Total do Jogo", f"{corners_calc['exc_total']} cantos")
        st.caption(f"Média Histórica (AVG): **{escanteios_avg}**")
    with col_e2:
        st.metric(f"🏠 ExC {match['time_casa']}", f"{corners_calc['exc_casa']} cantos")
        st.caption(f"Domínio Ofensivo: **{corners_calc['share_casa_pct']}%**")
    with col_e3:
        st.metric(f"✈️ ExC {match['time_visi']}", f"{corners_calc['exc_visi']} cantos")
        st.caption(f"Domínio Ofensivo: **{corners_calc['share_visi_pct']}%**")
    with col_e4:
        st.metric("📊 Média das Equipes (AVG)", f"{escanteios_avg} cantos")
        st.caption("Packball Nativo")
        
    st.caption(f"Proporção de Escanteios Esperados: **{match['time_casa']} ({corners_calc['exc_casa']})** vs **{match['time_visi']} ({corners_calc['exc_visi']})**")
    st.progress(corners_calc['share_casa_pct'] / 100.0)
    
    st.markdown("---")
    
    st.subheader("📈 Estatísticas Nativas e Oficiais do Packball VIP")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("🎯 Expectativa de Gols (ExG)", f"{exg_oficial} gols")
        st.caption(f"Média Histórica de Gols: **{gols_avg}**")
    with col_s2:
        st.metric("⚽ Ambas Marcam (BTS %)", f"{bts}")
        st.caption(f"Prob. Over 2.5 Gols: **{over25 if over25 else 'N/A'}**")
    with col_s3:
        st.metric("🏆 Prob. Vitória (% Win)", f"{win_prob}")
        st.caption("Projeção Packball")
    with col_s4:
        st.metric("📈 Pontos Por Jogo (PPG)", f"{ppg}")
        st.caption(f"Horário: **{horario}**")

    st.markdown("---")
    
    st.subheader("🛡️ Diagnóstico de Solidez Defensiva & Clean Sheet")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(f"#### Defesa {match['time_casa']}")
        st.progress(min(def_casa / 100.0, 1.0))
        st.write(f"🛡️ **Solidez Defensiva:** **{def_casa}%** &nbsp;|&nbsp; 🧤 **Clean Sheet:** **{cs_casa}%**")
    with col_d2:
        st.markdown(f"#### Defesa {match['time_visi']}")
        st.progress(min(def_visi / 100.0, 1.0))
        st.write(f"🛡️ **Solidez Defensiva:** **{def_visi}%** &nbsp;|&nbsp; 🧤 **Clean Sheet:** **{cs_visi}%**")
        
    st.markdown("---")

    # Diagnóstico com Google Gemini AI
    st.subheader("🤖 Diagnóstico Especialista com Google Gemini")
    from utils.gemini_assistant import analyze_match_with_gemini, get_api_key
    gemini_key = st.session_state.get("gemini_api_key") or get_api_key()
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
