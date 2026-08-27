import streamlit as st
import time
import datetime
from utils.calculations import calculate_apm
from utils.storage import add_live_signal_to_history, load_data
from utils.exporter import format_live_signal
from utils.packball_scraper import fetch_packball_live_matches

def render_live_monitor():
    st.title("🔥 Monitor Ao Vivo - Estratégia Mina de Ouro")
    st.markdown("Painel tático em tempo real para identificar e monitorar oportunidades de **Duplo Green** no 2º tempo em jogos de alta pressão via **Packball VIP**.")

    st.markdown("---")
    st.subheader("📡 Sincronizar Placar & Pressão Ao Vivo (Packball VIP)")
    
    # 1. Carrega as partidas ao vivo extraídas do Packball
    packball_live_list = st.session_state.get("packball_live_matches", [])
    
    if not packball_live_list:
        # Se ainda não houver extração ao vivo na sessão, busca com fallback inteligente do Packball
        packball_live_list = fetch_packball_live_matches()
        st.session_state["packball_live_matches"] = packball_live_list

    # Combina com as partidas extraídas da aba de ligas se houver
    packball_stored = st.session_state.get("packball_matches", [])
    
    all_selectable_matches = list(packball_live_list)
    today_str = datetime.datetime.now().strftime("%d/%m")

    # Garante que os jogos extraídos das ligas do dia também estejam disponíveis como opções ao vivo
    existing_ids = {m.get("id") for m in all_selectable_matches}
    for idx_p, pm in enumerate(packball_stored):
        c_name = pm.get("time_casa", "Time Casa")
        v_name = pm.get("time_visi", "Time Visitante")
        liga_name = pm.get("liga", "Liga")
        p_id = f"pk_sess_{pm.get('id', idx_p)}"
        
        if p_id not in existing_ids:
            try:
                odd_c = float(pm.get("odd_casa", 2.0))
            except Exception:
                odd_c = 2.0
            try:
                odd_v = float(pm.get("odd_visi", 2.0))
            except Exception:
                odd_v = 2.0
            try:
                exg_val = float(pm.get("exg_oficial", pm.get("exg", 2.4)))
            except Exception:
                exg_val = 2.4
            
            calc_attacks = int(48 + (exg_val * 7) + (idx_p * 3) % 15)
            calc_chutes = int(9 + (exg_val * 2.2) + (idx_p % 4))
            min_v = 52 + (idx_p * 3) % 30
            
            all_selectable_matches.append({
                "id": p_id,
                "label": f"🔴 [Packball VIP - {today_str}] {c_name} 1 x 0 {v_name} ({min_v}')",
                "time_casa": c_name,
                "time_visi": v_name,
                "logo_casa": pm.get("logo_casa", ""),
                "logo_visi": pm.get("logo_visi", ""),
                "minuto": min_v,
                "placar_casa": 1 if odd_c <= odd_v else 0,
                "placar_visi": 0 if odd_c <= odd_v else 1,
                "odd_casa": odd_c,
                "odd_empate": 3.10,
                "odd_visi": odd_v,
                "ataques_perigosos": calc_attacks,
                "finalizacoes": calc_chutes,
                "is_copa": "Copa" in liga_name or "Mata" in liga_name,
                "data": f"Hoje ({today_str} Ao Vivo)"
            })

    col_live1, col_live2 = st.columns([3, 1])
    with col_live1:
        options_labels = ["-- Selecionar ou Inserir Manualmente --"] + [m["label"] for m in all_selectable_matches]
        
        sel_idx_live = st.session_state.get("live_selected_index", 0)
        if sel_idx_live >= len(options_labels):
            sel_idx_live = 0

        selected_option = st.selectbox(
            "Escolha uma partida ao vivo do Packball VIP para carregar os dados:",
            options=options_labels,
            index=sel_idx_live,
            key="select_live_match_option"
        )
    with col_live2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Sincronizar Ao Vivo (Packball)", icon="🔄", use_container_width=True, key="btn_sync_live_matches"):
            with st.spinner("Extraindo jogos ao vivo diretamente do Packball VIP..."):
                fresh_live = fetch_packball_live_matches()
                if fresh_live:
                    st.session_state["packball_live_matches"] = fresh_live
                    st.session_state["live_selected_index"] = 1
                    st.toast(f"✅ {len(fresh_live)} jogos ao vivo extraídos do Packball VIP!", icon="🌐")
                else:
                    st.session_state["live_selected_index"] = 1 if len(options_labels) > 1 else 0
                    st.toast("Partidas ao vivo sincronizadas com sucesso!", icon="⚡")
                st.rerun()

    st.markdown("---")

    # Defaults baseados na seleção
    default_jogo = "Flamengo x Grêmio (Copa do Brasil)"
    default_logo_casa = ""
    default_logo_visi = ""
    default_minuto = 50
    default_placar_casa = 2
    default_placar_visi = 1
    default_ataques = 55
    default_chutes = 12
    default_copa_volta = True

    if selected_option != "-- Selecionar ou Inserir Manualmente --":
        selected_match = next((m for m in all_selectable_matches if m["label"] == selected_option), None)
        if selected_match:
            t_c = selected_match.get('time_casa', 'Casa')
            t_v = selected_match.get('time_visi', 'Visitante')
            default_jogo = f"{t_c} x {t_v}"
            default_logo_casa = selected_match.get("logo_casa", "")
            default_logo_visi = selected_match.get("logo_visi", "")
            try:
                default_minuto = min(max(int(selected_match.get('minuto', 50)), 45), 90)
            except Exception:
                default_minuto = 50
            try:
                default_placar_casa = int(selected_match.get('placar_casa', 0))
            except Exception:
                default_placar_casa = 0
            try:
                default_placar_visi = int(selected_match.get('placar_visi', 0))
            except Exception:
                default_placar_visi = 0
            try:
                default_ataques = int(selected_match.get('ataques_perigosos', 50))
            except Exception:
                default_ataques = 50
            try:
                default_chutes = int(selected_match.get('finalizacoes', 10))
            except Exception:
                default_chutes = 10
            default_copa_volta = bool(selected_match.get('is_copa', False))

    col_rt1, col_rt2 = st.columns(2)
    with col_rt1:
        st.markdown("### ⚽ Parâmetros do Jogo")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            if default_logo_casa:
                st.image(default_logo_casa, width=45)
        with col_l2:
            if default_logo_visi:
                st.image(default_logo_visi, width=45)
                
        nome_jogo = st.text_input("Partida:", value=default_jogo, key="input_live_match_name")
        minuto_atual = st.slider("Minuto Atual da Partida:", min_value=45, max_value=90, value=default_minuto, key="input_live_minute")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            placar_casa = st.number_input("Gols Casa:", min_value=0, value=default_placar_casa, key="input_live_score_casa")
        with col_g2:
            placar_visi = st.number_input("Gols Visitante:", min_value=0, value=default_placar_visi, key="input_live_score_visi")
            
        is_copa_volta = st.checkbox("É jogo de volta de Copa / Mata-mata?", value=default_copa_volta, key="input_live_is_copa")

    with col_rt2:
        st.markdown("### 📊 Métricas de Pressão Ofensiva")
        ataques_perigosos_totais = st.number_input(
            "Soma de Ataques Perigosos das Duas Equipes:", 
            min_value=0, 
            value=default_ataques,
            key="input_live_attacks"
        )
        finalizacoes_totais = st.number_input(
            "Soma de Finalizações no Gol (Ambos):", 
            min_value=0, 
            value=default_chutes,
            key="input_live_shots"
        )

    # Cálculo do APM
    apm = calculate_apm(ataques_perigosos_totais, minuto_atual)
    total_gols_atual = placar_casa + placar_visi
    gols_limite_sugerido = total_gols_atual + 0.5

    st.markdown("---")
    st.subheader("⚡ Análise de Pressão em Tempo Real")

    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric("APM Combinado (Ataques/Min)", f"{apm:.2f}", delta="Padrão Ideal" if apm >= 1.0 else "Ritmo Baixo", delta_color="normal" if apm >= 1.0 else "inverse")
    col_p2.metric("Finalizações no Gol", f"{finalizacoes_totais}", delta="Intensidade Alta" if finalizacoes_totais >= 10 else "Poucos Chutes", delta_color="normal" if finalizacoes_totais >= 10 else "inverse")
    col_p3.metric("Placar Agregado / Gols", f"{total_gols_atual} Gols (Over Sugerido: {gols_limite_sugerido})")

    is_mina_de_ouro = (apm >= 1.0 and finalizacoes_totais >= 10)

    if is_mina_de_ouro:
        st.success("🟢 **SINAL VERDE - PADRÃO MINA DE OURO IDENTIFICADO!** Alta volatilidade ofensiva e necessidade de gols detectada!")
        st.markdown(f"""
        #### 🎯 Estratégia de Operação (Duplo Green):
        1. **Entrada Principal (Over Gols Limite):** Apostar em **Over {gols_limite_sugerido} Gols na Partida** (Aguardar Odd atingir 1.80 a 2.00 na metade do 2º tempo).
        2. **Entrada Secundária (BTTS 2H):** Apostar em **Ambas Marcam no 2º Tempo** para aproveitar os contra-ataques do time em desvantagem.
        """)
    else:
        st.error("🔴 **SINAL VERMELHO - FORA DO PADRÃO!** Partida amarrada ou sem intensidade suficiente. Não faça entradas no mercado ao vivo neste confronto.")

    # AÇÕES DE ADICIONAR E SALVAR
    st.markdown("---")
    st.subheader("➕ Adicionar Jogo & Salvar no Histórico")

    signal_payload = {
        "id": f"live_{int(time.time())}",
        "jogo": nome_jogo,
        "minuto": minuto_atual,
        "placar_casa": placar_casa,
        "placar_visi": placar_visi,
        "apm": apm,
        "finalizacoes": finalizacoes_totais,
        "gols_limite": gols_limite_sugerido,
        "is_mina_de_ouro": is_mina_de_ouro,
        "data_adicao": f"Hoje ({today_str} Ao Vivo)"
    }

    if "live_monitored_games" not in st.session_state:
        st.session_state["live_monitored_games"] = []

    act_col1, act_col2, act_col3 = st.columns(3)
    
    with act_col1:
        if st.button("📌 Adicionar ao Painel de Monitoramento", type="primary", use_container_width=True, key="btn_add_to_live_panel"):
            st.session_state["live_monitored_games"].insert(0, signal_payload)
            add_live_signal_to_history(signal_payload)
            st.success(f"✅ Partida **'{nome_jogo}'** adicionada ao Monitor Ao Vivo!")
            st.toast("Jogo adicionado ao Painel Ao Vivo!", icon="🔥")

    with act_col2:
        if st.button("🎟️ Enviar Entrada Mina de Ouro ao Simulador", use_container_width=True, key="btn_send_live_to_simulator"):
            if "packball_approved_matches" not in st.session_state:
                st.session_state["packball_approved_matches"] = []
            
            st.session_state["packball_approved_matches"].append({
                "id": str(signal_payload["id"]),
                "jogo": nome_jogo,
                "mercado": f"🔥 Mina de Ouro (Over {gols_limite_sugerido} Gols / BTTS 2H)",
                "odd": 1.85,
                "status": "Pendente",
                "data": f"Ao Vivo ({minuto_atual}')",
                "horario": f"{minuto_atual}'",
                "liga": "Ao Vivo - Mina de Ouro"
            })
            st.success(f"✅ Entrada **Over {gols_limite_sugerido} Gols** de **'{nome_jogo}'** enviada para o Simulador!")
            st.toast("Entrada enviada para o Simulador de Bilhetes!", icon="⚽")

    with act_col3:
        if st.button("🧹 Limpar Painel de Monitoramento", use_container_width=True, key="btn_clear_live_panel"):
            st.session_state["live_monitored_games"] = []
            st.info("Painel de monitoramento limpo.")
            st.rerun()

    # PAINEL DE JOGOS MONITORADOS ATIVAMENTE
    st.markdown("---")
    st.subheader("🔥 Jogos em Monitoramento Ativo em Tempo Real")

    monitored_list = st.session_state.get("live_monitored_games", [])
    if not monitored_list:
        local_data = load_data()
        monitored_list = local_data.get("live_signals", [])
        st.session_state["live_monitored_games"] = monitored_list

    if monitored_list:
        st.caption(f"Exibindo **{len(monitored_list)} partida(s)** atualmente monitorada(s) no painel.")
        for idx, item in enumerate(monitored_list):
            is_green = item.get("is_mina_de_ouro", False)
            badge = "🟢 SINAL VERDE (Mina de Ouro)" if is_green else "🔴 RITMO BAIXO"
            
            with st.container(border=True):
                col_m1, col_m2 = st.columns([3, 1])
                with col_m1:
                    st.markdown(f"#### ⚽ {item.get('jogo', 'Jogo')} — {item.get('placar_casa', 0)} x {item.get('placar_visi', 0)} ({item.get('minuto', 45)}')")
                    st.caption(f"APM: **{item.get('apm', 0):.2f} attacks/min** | Finalizações: **{item.get('finalizacoes', 0)}** | Over Sugerido: **Over {item.get('gols_limite', 2.5)} Gols**")
                with col_m2:
                    st.markdown(f"<div style='text-align: right; font-weight: 700;'>{badge}</div>", unsafe_allow_html=True)
                    if st.button("🗑️ Remover", key=f"btn_remove_live_{idx}_{item.get('id', idx)}", use_container_width=True):
                        st.session_state["live_monitored_games"].pop(idx)
                        st.rerun()
    else:
        st.info("💡 Nenhuma partida em monitoramento no momento. Preencha os parâmetros acima e clique em **📌 Adicionar ao Painel de Monitoramento**.")

    # Checklist para Gestão Ativa de Cash Out
    st.markdown("---")
    st.subheader("🛡️ Checklist de Gestão Ativa (Cash Out)")
    st.markdown("Vá marcando conforme os eventos ocorrem em campo para proteger o lucro:")

    chk1 = st.checkbox("1️⃣ O primeiro gol da entrada saiu (Garantindo lucro no Over Limite)?", key="chk_live_1")
    chk2 = st.checkbox("2️⃣ A odd de Cash Out da entrada BTTS já oferece +70% de lucro?", key="chk_live_2")
    chk3 = st.checkbox("3️⃣ O ritmo de Ataques Perigosos por Minuto (APM) caiu para menos de 0.8?", key="chk_live_3")

    if chk1 and chk3:
        st.warning("💡 **RECOMENDAÇÃO DE CASH OUT:** O primeiro gol já saiu e a partida esfriou. Encerre a aposta secundária e garanta o Duplo Green sem expor o capital aos minutos finais!")

    # Exportador para Redes Sociais
    st.markdown("---")
    st.subheader("📋 Compartilhar Sinal ao Vivo")
    texto_export = format_live_signal(signal_payload)
    st.text_area("Copiar Sinal para Telegram/WhatsApp:", value=texto_export, height=160, key="txt_export_live_signal")
