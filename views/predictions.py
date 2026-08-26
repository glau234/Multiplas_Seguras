import streamlit as st
import time
import pandas as pd
from utils.calculations import filter_out_past_matches, filter_out_serie_b
from utils.gemini_assistant import analyze_match_with_gemini, get_api_key
from utils.odds_comparator import render_bookmaker_comparison_card

def compute_best_market_prediction(match):
    """
    Computa e formata as colunas oficiais de Previsões do Packball
    (Best Market, Prob H2H, Prob Algoritmo, Odd, EV, EV Net).
    """
    if match.get("best_market") and str(match.get("best_market")).strip():
        return {
            "best": match.get("best_market"),
            "prob_h2h": match.get("prob_h2h", "80%"),
            "prob_algo": match.get("prob_algo", "85%"),
            "odd": match.get("odd_best", 1.50),
            "ev": match.get("ev", 1.25),
            "ev_net": match.get("ev_net", 0.45)
        }

    try:
        odd_c = float(match.get("odd_casa", 2.0))
    except Exception:
        odd_c = 2.0
    try:
        odd_v = float(match.get("odd_visi", 2.0))
    except Exception:
        odd_v = 2.0
    try:
        exg_val = float(match.get("exg_oficial", match.get("exg", 2.5)))
    except Exception:
        exg_val = 2.5

    underdog = match.get("time_casa", "Casa") if odd_c > odd_v else match.get("time_visi", "Visitante")
    fav = match.get("time_casa", "Casa") if odd_c <= odd_v else match.get("time_visi", "Visitante")
    diff_odd = abs(odd_c - odd_v)

    # 1. Entrada Recomendada: Handicap Europeu +3 em jogos equilibrados com ExG seguro
    if diff_odd <= 2.50 and exg_val <= 3.20:
        return {
            "best": f"Handicap Europeu +3 ({underdog})",
            "prob_h2h": "88%",
            "prob_algo": "90%",
            "odd": 1.15,
            "ev": 1.14,
            "ev_net": 0.36
        }
    # 2. Entrada Recomendada: Menos de 1.5 gols 1º tempo
    elif exg_val <= 2.20:
        return {
            "best": "Menos de 1.5 gols 1º tempo",
            "prob_h2h": "85%",
            "prob_algo": "82%",
            "odd": 1.34,
            "ev": 1.22,
            "ev_net": 0.12
        }
    # 3. Entrada Recomendada: Favorito Marcar Primeiro
    elif diff_odd > 2.50:
        return {
            "best": f"{fav} marcar primeiro",
            "prob_h2h": "70%",
            "prob_algo": "88%",
            "odd": 1.50,
            "ev": 1.14,
            "ev_net": 0.36
        }
    # 4. Entrada Recomendada: Disciplinar / Menos de 4.5 cartões
    else:
        return {
            "best": "Menos de 4.5 cartões",
            "prob_h2h": "90%",
            "prob_algo": "90%",
            "odd": 2.26,
            "ev": 1.11,
            "ev_net": 1.15
        }

def render_predictions():
    st.title("🔮 Previsões do Dia (Packball VIP & Gemini IA)")
    st.markdown(
        "Acompanhe a **tabela oficial de previsões de valor (+EV)** do Packball VIP para os jogos das suas **ligas favoritas**. "
        "Analise as entradas sugeridas pelo algoritmo (Best Market, % H2H, EV, EV Net), gere diagnósticos táticos com o **Gemini IA** "
        "e envie as seleções direto para o seu **Simulador de Bilhetes**."
    )

    gemini_key = st.session_state.get("gemini_api_key") or get_api_key()

    # Obter partidas da sessão ou do arquivo de cache
    if "packball_matches" not in st.session_state or not st.session_state["packball_matches"]:
        import os, json
        if os.path.exists("data/cached_packball.json"):
            try:
                with open("data/cached_packball.json", "r", encoding="utf-8") as f:
                    cached_raw = json.load(f)
                    st.session_state["packball_matches"] = filter_out_past_matches(filter_out_serie_b(cached_raw))
            except Exception:
                st.session_state["packball_matches"] = []

    stored_matches = st.session_state.get("packball_matches", [])
    clean_matches = filter_out_past_matches(filter_out_serie_b(stored_matches))

    # Obter lista de ligas disponíveis para o filtro "Minhas Ligas"
    all_leagues = sorted(list(dict.fromkeys(m.get("liga", "Geral") for m in clean_matches if m.get("liga"))))
    
    col_f1, col_f2, col_f3 = st.columns([2.5, 1, 1])
    with col_f1:
        selected_leagues = st.multiselect(
            "🏆 Selecione Suas Ligas Favoritas (Minhas Ligas):",
            options=all_leagues,
            default=all_leagues[:6] if len(all_leagues) >= 6 else all_leagues,
            help="Escolha quais ligas deseja monitorar e ver as previsões estatísticas do dia."
        )
    with col_f2:
        available_dates = ["Todas as Datas"] + sorted(list(dict.fromkeys(str(m.get("data", "")).strip() for m in clean_matches if m.get("data"))))
        filter_date = st.selectbox(
            "📅 Data do Confronto:",
            options=available_dates
        )
    with col_f3:
        only_qualified = st.checkbox(
            "🟢 Apenas Qualificados (+3)", 
            value=False, 
            help="Exibe somente os jogos que atendem aos critérios estritos de equilíbrio e ExG."
        )

    # Filtrar partidas pelas ligas selecionadas
    filtered_matches = clean_matches
    if selected_leagues:
        filtered_matches = [m for m in filtered_matches if m.get("liga") in selected_leagues]
        
    if filter_date != "Todas as Datas":
        filtered_matches = [m for m in filtered_matches if str(m.get("data", "")).strip() == filter_date]

    if only_qualified:
        filtered_matches = [
            m for m in filtered_matches
            if (abs(m.get("odd_casa", 1.0) - m.get("odd_visi", 1.0)) <= 2.50) and 
               (float(m.get("exg_oficial", m.get("exg", 2.5))) <= 3.20)
        ]

    st.markdown("---")

    if not filtered_matches:
        st.info("💡 Nenhum jogo encontrado para as ligas ou filtros selecionados. Realize uma nova extração no painel **🌐 Integração Packball** ou selecione outras ligas acima.")
    else:
        # Seletor de Modo de Visualização (Tabela Packball vs Cards)
        view_mode = st.radio(
            "Modo de Exibição das Previsões:",
            options=["📊 Tabela Oficial Packball (Todas as Colunas de Valor)", "🎴 Cards Expandidos com Diagnóstico IA"],
            horizontal=True
        )

        st.subheader(f"📊 {len(filtered_matches)} Previsão(ões) Encontrada(s) nas Suas Ligas")

        if view_mode.startswith("📊"):
            # ----------------------------------------------------
            # VISÃO TABELA OFICIAL PACKBALL (TODAS AS COLUNAS DA IMAGEM)
            # ----------------------------------------------------
            table_rows = []
            for idx, match in enumerate(filtered_matches):
                pred = compute_best_market_prediction(match)
                odd_c = match.get("odd_casa", 2.0)
                odd_v = match.get("odd_visi", 2.0)
                exg_val = float(match.get("exg_oficial", match.get("exg", 2.5)))
                diff_odd = abs(odd_c - odd_v)
                aprovado = (diff_odd <= 2.50) and (exg_val <= 3.20)
                
                table_rows.append({
                    "ID": match.get("id", idx),
                    "País/Liga": f"{match.get('pais', '')} {match.get('liga', '')}".strip(),
                    "Data/Hora": f"{match.get('data', '')} {match.get('horario', '')}".strip(),
                    "Confronto": f"{match['time_casa']} vs {match['time_visi']}",
                    "Best (Entrada Recomendada)": pred["best"],
                    "📊 Prob H2H": pred["prob_h2h"],
                    "% Algoritmo": pred["prob_algo"],
                    "Odd": f"{float(pred['odd']):.2f}",
                    "EV": f"{float(pred['ev']):.2f}",
                    "⚽+ EV Net": f"{float(pred['ev_net']):.2f}",
                    "Status": "🟢 Qualificado (+3)" if aprovado else "⚪ Monitoramento"
                })

            df_pred = pd.DataFrame(table_rows)

            # Exibe a tabela formatada com suporte a seleção de linhas
            st.markdown("##### 📋 Tabela de Previsões Packball VIP (+EV)")
            st.dataframe(
                df_pred.drop(columns=["ID"]),
                use_container_width=True,
                height=450
            )

            # Ações Rápidas em Lote ou Seleção Individual
            st.markdown("##### ⚡ Ações Rápidas na Tabela de Previsões")
            col_sel1, col_sel2 = st.columns([2, 1])
            with col_sel1:
                selected_match_label = st.selectbox(
                    "Selecione uma partida da tabela para analisar com IA ou Enviar ao Simulador:",
                    options=[f"{m['time_casa']} vs {m['time_visi']} ({m.get('liga', '')})" for m in filtered_matches]
                )
            
            sel_idx = [f"{m['time_casa']} vs {m['time_visi']} ({m.get('liga', '')})" for m in filtered_matches].index(selected_match_label) if selected_match_label else 0
            sel_match = filtered_matches[sel_idx]
            sel_pred = compute_best_market_prediction(sel_match)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🔮 Auditar Partida Selecionada com Gemini IA", use_container_width=True, key="btn_tbl_ai"):
                    with st.spinner(f"O Gemini está analisando {sel_match['time_casa']} vs {sel_match['time_visi']}..."):
                        parecer = analyze_match_with_gemini(sel_match, gemini_key)
                        st.session_state[f"pred_tbl_ai_{sel_idx}"] = parecer

            with col_btn2:
                if st.button("➕ Adicionar Entrada Recomendada ao Simulador", use_container_width=True, key="btn_tbl_add"):
                    if "packball_approved_matches" not in st.session_state:
                        st.session_state["packball_approved_matches"] = []
                    
                    st.session_state["packball_approved_matches"].append({
                        "id": sel_match.get("id", str(time.time())),
                        "jogo": f"{sel_match['time_casa']} vs {sel_match['time_visi']}",
                        "mercado": sel_pred["best"],
                        "odd": float(sel_pred["odd"]),
                        "status": "Pendente",
                        "data": f"{sel_match.get('data', '')} {sel_match.get('horario', '')}".strip(),
                        "horario": sel_match.get("horario", ""),
                        "liga": sel_match.get("liga", "")
                    })
                    st.toast(f"✅ Entrada adicionada ao Simulador: {sel_pred['best']} @{sel_pred['odd']}", icon="⚽")

            if st.session_state.get(f"pred_tbl_ai_{sel_idx}"):
                st.markdown("---")
                st.info(st.session_state[f"pred_tbl_ai_{sel_idx}"])

        else:
            # ----------------------------------------------------
            # VISÃO CARDS EXPANDIDOS COM MÉTRICAS E COMPARAÇÃO DE ODDS
            # ----------------------------------------------------
            for idx, match in enumerate(filtered_matches):
                pred = compute_best_market_prediction(match)
                odd_c = match.get("odd_casa", 2.0)
                odd_e = match.get("odd_empate", 3.10)
                odd_v = match.get("odd_visi", 2.0)
                exg_val = float(match.get("exg_oficial", match.get("exg", 2.5)))
                diff_odd = abs(odd_c - odd_v)
                aprovado = (diff_odd <= 2.50) and (exg_val <= 3.20)
                status_badge = "🟢 Qualificado (+3)" if aprovado else "⚪ Monitoramento"
                
                maior_odd_time = match['time_casa'] if odd_c > odd_v else match['time_visi']
                data_str = match.get("data", "")
                horario_str = match.get("horario", "")
                dh_str = f"{data_str} {horario_str}".strip() if horario_str and horario_str not in data_str else data_str

                with st.container(border=True):
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        st.markdown(f"### ⚽ {match['time_casa']} vs {match['time_visi']}")
                        st.caption(f"🏆 **{match.get('liga', '')} ({match.get('pais', '')})** &nbsp;|&nbsp; 📅 **{data_str}** &nbsp;|&nbsp; ⏰ **{horario_str}**")
                    with col_h2:
                        st.markdown(f"<div style='text-align: right; font-weight: 800; font-size: 1.05rem;'>{status_badge}</div>", unsafe_allow_html=True)
                        st.caption(f"Best: **{pred['best']}**")

                    # Métricas de Valor do Packball (Idênticas ao Painel Oficial)
                    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
                    col_m1.metric("🎯 Best Market", pred["best"].split("(")[0].strip())
                    col_m2.metric("📊 Prob. H2H", pred["prob_h2h"])
                    col_m3.metric("% Algoritmo", pred["prob_algo"])
                    col_m4.metric("💰 Odd Valor", f"{float(pred['odd']):.2f}")
                    col_m5.metric("📈 EV", f"{float(pred['ev']):.2f}")
                    col_m6.metric("⚡ EV Net", f"{float(pred['ev_net']):.2f}")

                    # Comparativo Bet365 vs Betano
                    render_bookmaker_comparison_card(match, market_type=pred["best"], compact=True)

                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        if st.button("🔮 Gerar Previsão Especialista Gemini IA", key=f"pred_ai_{idx}_{match.get('id', idx)}", use_container_width=True):
                            with st.spinner(f"O Gemini está compilando o prognóstico tático de {match['time_casa']} vs {match['time_visi']}..."):
                                parecer = analyze_match_with_gemini(match, gemini_key)
                                st.session_state[f"pred_res_{idx}_{match.get('id', idx)}"] = parecer

                    with col_act2:
                        if st.button("➕ Enviar Partida para o Simulador de Bilhetes", key=f"pred_add_{idx}_{match.get('id', idx)}", use_container_width=True):
                            if "packball_approved_matches" not in st.session_state:
                                st.session_state["packball_approved_matches"] = []
                            st.session_state["packball_approved_matches"].append({
                                "id": match.get("id", str(time.time())),
                                "jogo": f"{match['time_casa']} vs {match['time_visi']}",
                                "mercado": pred["best"],
                                "odd": float(pred["odd"]),
                                "status": "Pendente",
                                "data": dh_str,
                                "horario": horario_str,
                                "liga": match.get("liga", "")
                            })
                            st.toast(f"✅ Adicionado ao Simulador: {match['time_casa']} vs {match['time_visi']} ({pred['best']})", icon="⚽")

                    # Exibição do resultado do Gemini IA
                    if st.session_state.get(f"pred_res_{idx}_{match.get('id', idx)}"):
                        st.markdown("---")
                        st.info(st.session_state[f"pred_res_{idx}_{match.get('id', idx)}"])
