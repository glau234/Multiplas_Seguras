import streamlit as st
from utils.calculations import calculate_apm
from utils.storage import add_live_signal_to_history
from utils.exporter import format_live_signal
from utils.football_api import fetch_todays_matches

def render_live_monitor():
    st.title("🔥 Monitor Ao Vivo - Estratégia Mina de Ouro")
    st.markdown("Painel tático em tempo real para identificar oportunidades de **Duplo Green** no 2º tempo em jogos de alta pressão.")

    st.markdown("---")
    st.subheader("📡 Sincronizar Placar & Pressão Ao Vivo (API)")
    
    api_key = st.session_state.get("api_key", "5555576d9dcbeed51c0625dcad03a722")
    todays_matches = fetch_todays_matches(api_key)
    
    col_live1, col_live2 = st.columns([3, 1])
    with col_live1:
        options_labels = ["-- Selecionar ou Inserir Manualmente --"] + [m["label"] for m in todays_matches]
        selected_option = st.selectbox("Escolha uma partida ao vivo para carregar os dados:", options_labels, index=0)
    with col_live2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sincronizar Ao Vivo", icon="🔄", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Defaults
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
        selected_match = next((m for m in todays_matches if m["label"] == selected_option), None)
        if selected_match:
            default_jogo = f"{selected_match['time_casa']} x {selected_match['time_visi']}"
            default_logo_casa = selected_match.get("logo_casa", "")
            default_logo_visi = selected_match.get("logo_visi", "")
            default_minuto = min(max(int(selected_match['minuto']), 45), 90)
            default_placar_casa = int(selected_match['placar_casa'])
            default_placar_visi = int(selected_match['placar_visi'])
            default_ataques = int(selected_match['ataques_perigosos'])
            default_chutes = int(selected_match['finalizacoes'])
            default_copa_volta = bool(selected_match['is_copa'])

    col_rt1, col_rt2 = st.columns(2)
    with col_rt1:
        st.markdown("### ⚽ Parâmetros do Jogo")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            if default_logo_casa:
                st.image(default_logo_casa, width=50)
        with col_l2:
            if default_logo_visi:
                st.image(default_logo_visi, width=50)
                
        nome_jogo = st.text_input("Partida:", default_jogo)
        minuto_atual = st.slider("Minuto Atual da Partida:", min_value=45, max_value=90, value=default_minuto)
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            placar_casa = st.number_input("Gols Casa:", min_value=0, value=default_placar_casa)
        with col_g2:
            placar_visi = st.number_input("Gols Visitante:", min_value=0, value=default_placar_visi)
            
        is_copa_volta = st.checkbox("É jogo de volta de Copa / Mata-mata?", value=default_copa_volta)

    with col_rt2:
        st.markdown("### 📊 Métricas de Pressão Ofensiva")
        ataques_perigosos_totais = st.number_input(
            "Soma de Ataques Perigosos das Duas Equipes:", 
            min_value=0, 
            value=default_ataques
        )
        finalizacoes_totais = st.number_input(
            "Soma de Finalizações no Gol (Ambos):", 
            min_value=0, 
            value=default_chutes
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
    col_p3.metric("Placar Agregado / Gols", f"{total_gols_atual} Gols")

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

    # Checklist para Gestão Ativa de Cash Out
    st.markdown("---")
    st.subheader("🛡️ Checklist de Gestão Ativa (Cash Out)")
    st.markdown("Vá marcando conforme os eventos ocorrem em campo para proteger o lucro:")

    chk1 = st.checkbox("1️⃣ O primeiro gol da entrada saiu (Garantindo lucro no Over Limite)?")
    chk2 = st.checkbox("2️⃣ A odd de Cash Out da entrada BTTS já oferece +70% de lucro?")
    chk3 = st.checkbox("3️⃣ O ritmo de Ataques Perigosos por Minuto (APM) caiu para menos de 0.8?")

    if chk1 and chk3:
        st.warning("💡 **RECOMENDAÇÃO DE CASH OUT:** O primeiro gol já saiu e a partida esfriou. Encerre a aposta secundária e garanta o Duplo Green sem expor o capital aos minutos finais!")

    # Exportação e Salvamento
    st.markdown("---")
    signal_payload = {
        "jogo": nome_jogo,
        "minuto": minuto_atual,
        "placar_casa": placar_casa,
        "placar_visi": placar_visi,
        "apm": apm,
        "finalizacoes": finalizacoes_totais,
        "is_mina_de_ouro": is_mina_de_ouro
    }

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("💾 Salvar Sinal no Histórico Local", use_container_width=True):
            if add_live_signal_to_history(signal_payload):
                st.toast("Sinal ao vivo salvo!", icon="🔥")
            else:
                st.error("Erro ao salvar sinal.")

    with col_s2:
        texto_export = format_live_signal(signal_payload)
        st.text_area("📋 Copiar Sinal para Telegram/WhatsApp:", value=texto_export, height=160)
