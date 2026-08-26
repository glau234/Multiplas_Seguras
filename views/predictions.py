import streamlit as st
import time
from utils.calculations import filter_out_past_matches, filter_out_serie_b
from utils.gemini_assistant import analyze_match_with_gemini, get_api_key
from utils.odds_comparator import render_bookmaker_comparison_card

def render_predictions():
    st.title("🔮 Previsões do Dia (Packball VIP & Gemini IA)")
    st.markdown(
        "Acompanhe as previsões estatísticas oficiais e o diagnóstico dos próximos jogos das suas **ligas favoritas**. "
        "Filtre por campeonato, analise as expectativas de gols/escanteios, consulte a Inteligência Artificial do Gemini "
        "e envie as melhores partidas diretamente para o seu **Simulador de Bilhetes**."
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
        st.subheader(f"📊 {len(filtered_matches)} Previsão(ões) Encontrada(s) nas Suas Ligas")
        
        for idx, match in enumerate(filtered_matches):
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
                    st.caption(f"Entrada Sugerida: **HE +3 ({maior_odd_time})**")

                col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                col_m1.metric(f"Vitória {match['time_casa']}", f"{odd_c:.2f}")
                col_m2.metric("Empate", f"{odd_e:.2f}")
                col_m3.metric(f"Vitória {match['time_visi']}", f"{odd_v:.2f}")
                col_m4.metric("ExG Oficial", f"{exg_val} gols")
                col_m5.metric("Ambas Marcam", f"{match.get('bts', 'N/A')}")

                # Comparativo Bet365 vs Betano
                render_bookmaker_comparison_card(match, market_type="Handicap Europeu +3", compact=True)

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
                            "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                            "odd": 1.15,
                            "status": "Pendente",
                            "data": dh_str,
                            "horario": horario_str,
                            "liga": match.get("liga", "")
                        })
                        st.toast(f"✅ Adicionado ao Simulador: {match['time_casa']} vs {match['time_visi']}", icon="⚽")

                # Exibição do resultado do Gemini IA
                if st.session_state.get(f"pred_res_{idx}_{match.get('id', idx)}"):
                    st.markdown("---")
                    st.info(st.session_state[f"pred_res_{idx}_{match.get('id', idx)}"])
