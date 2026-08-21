import streamlit as st
from utils.calculations import calculate_implied_probability, calculate_ev, check_match_balance
from utils.storage import add_match_to_history
from utils.exporter import format_match_analysis
from utils.football_api import fetch_todays_matches

def render_match_analyzer():
    st.title("🔍 Analisador de Partidas - Método Múltiplas Seguras")
    st.markdown("Insira ou **carregue automaticamente** os dados pré-live para validar a conformidade da partida com os critérios estritos do método.")

    st.markdown("---")
    st.subheader("⚡ Carregar Partida da Rodada (API em Tempo Real)")
    
    api_key = st.session_state.get("api_key", "5555576d9dcbeed51c0625dcad03a722")
    todays_matches = fetch_todays_matches(api_key)
    
    col_api1, col_api2 = st.columns([3, 1])
    with col_api1:
        options_labels = ["-- Selecionar ou Inserir Manualmente --"] + [m["label"] for m in todays_matches]
        selected_option = st.selectbox(
            "Escolha um jogo para carregar automaticamente os dados:", 
            options_labels,
            index=0
        )
    with col_api2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Atualizar API", icon="🔄", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Defaults baseados na seleção
    default_casa = "Vasco da Gama"
    default_visi = "Santos"
    default_logo_casa = ""
    default_logo_visi = ""
    default_odd_casa = 2.72
    default_odd_empate = 3.10
    default_odd_visi = 2.75
    default_xg = 1.70
    default_cs_casa = 45
    default_cs_visi = 40
    default_h2h_casa = 35
    default_h2h_empate = 30
    default_h2h_visi = 35
    default_copa = False
    default_volta = False
    default_vantagem = False

    if selected_option != "-- Selecionar ou Inserir Manualmente --":
        selected_match = next((m for m in todays_matches if m["label"] == selected_option), None)
        if selected_match:
            default_casa = selected_match["time_casa"]
            default_visi = selected_match["time_visi"]
            default_logo_casa = selected_match.get("logo_casa", "")
            default_logo_visi = selected_match.get("logo_visi", "")
            default_odd_casa = float(selected_match["odd_casa"])
            default_odd_empate = float(selected_match["odd_empate"])
            default_odd_visi = float(selected_match["odd_visi"])
            default_xg = float(selected_match["xg_partida"])
            default_cs_casa = int(selected_match["clean_sheets_casa"])
            default_cs_visi = int(selected_match["clean_sheets_visi"])
            default_h2h_casa = int(selected_match["h2h_casa"])
            default_h2h_empate = int(selected_match["h2h_empate"])
            default_h2h_visi = int(selected_match["h2h_visi"])
            default_copa = bool(selected_match["is_copa"])
            default_volta = bool(selected_match["is_volta"])
            default_vantagem = bool(selected_match["tem_vantagem"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏟️ Dados do Confronto")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            if default_logo_casa:
                st.image(default_logo_casa, width=50)
            time_casa = st.text_input("Time da Casa:", default_casa)
        with col_l2:
            if default_logo_visi:
                st.image(default_logo_visi, width=50)
            time_visi = st.text_input("Time Visitante:", default_visi)
        
        col_odd1, col_odd2, col_odd3 = st.columns(3)
        with col_odd1:
            odd_casa = st.number_input("Odd Casa:", min_value=1.01, value=default_odd_casa, step=0.01)
        with col_odd2:
            odd_empate = st.number_input("Odd Empate:", min_value=1.01, value=default_odd_empate, step=0.01)
        with col_odd3:
            odd_visi = st.number_input("Odd Visitante:", min_value=1.01, value=default_odd_visi, step=0.01)
            
    with col2:
        st.markdown("### 📊 Métricas Táticas e Contexto")
        xg_partida = st.number_input("Expectativa de Gols Projetada (xG da Partida):", min_value=0.0, value=default_xg, step=0.10)
        
        col_cs1, col_cs2 = st.columns(2)
        with col_cs1:
            clean_sheets_casa = st.slider("% Clean Sheets Casa:", 0, 100, default_cs_casa)
        with col_cs2:
            clean_sheets_visi = st.slider("% Clean Sheets Visitante:", 0, 100, default_cs_visi)
            
        st.markdown("**Histórico H2H (% Vitórias)**")
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            h2h_casa = st.number_input("% Vitória Casa (H2H):", 0, 100, default_h2h_casa)
        with col_h2:
            h2h_empate = st.number_input("% Empate (H2H):", 0, 100, default_h2h_empate)
        with col_h3:
            h2h_visi = st.number_input("% Vitória Visitante (H2H):", 0, 100, default_h2h_visi)

        is_copa = st.checkbox("É jogo de Copa / Mata-mata?", value=default_copa)
        is_volta = False
        tem_vantagem = False
        if is_copa:
            is_volta = st.checkbox("É o jogo de VOLTA da eliminatória?", value=default_volta)
            tem_vantagem = st.checkbox("Uma das equipes tem grande vantagem do jogo de ida?", value=default_vantagem)

    st.markdown("---")
    st.subheader("📋 Diagnóstico e Recomendações do Método")

    # Análise de Equilíbrio
    is_parelho, diff_odd = check_match_balance(odd_casa, odd_visi)
    maior_odd_time = time_casa if odd_casa > odd_visi else time_visi
    maior_odd_valor = max(odd_casa, odd_visi)
    maior_odd_h2h = h2h_casa if odd_casa > odd_visi else h2h_visi

    # Probabilidades Implícitas e +EV
    prob_implicita = calculate_implied_probability(maior_odd_valor)
    ev_percent = calculate_ev(maior_odd_h2h + (h2h_empate * 0.5), maior_odd_valor)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Diferença de Odds", f"{diff_odd:.2f}", delta="Parelho" if is_parelho else "Desequilibrado", delta_color="normal" if is_parelho else "inverse")
    col_m2.metric("xG Projetado", f"{xg_partida:.2f} gols", delta="Dentro do Limite" if xg_partida <= 2.0 else "Alto Risco", delta_color="normal" if xg_partida <= 2.0 else "inverse")
    col_m3.metric("Probabilidade Implícita", f"{prob_implicita:.1f}%")
    col_m4.metric("Valor Esperado (+EV)", f"{ev_percent:+.1f}%", delta="Com Valor" if ev_percent > 0 else "Sem EV+", delta_color="normal" if ev_percent > 0 else "inverse")

    diagnostico_status = ""
    recomendacao_texto = ""

    if is_copa:
        if not is_volta:
            st.error("🚨 **VIOLAÇÃO DO MÉTODO DE COPAS:** Jogos de ida em copas são altamente imprevisíveis e cheios de volatilidade. O método preconiza APENAS jogos de volta!")
            diagnostico_status = "REPROVADO - Copa Jogo de Ida"
            recomendacao_texto = "Evitar entrada pré-live. Aguardar o jogo de volta."
        elif is_volta and tem_vantagem:
            st.success("✅ **CENÁRIO DE COPA VÁLIDO!** Jogo de volta com vantagem construída.")
            diagnostico_status = "APROVADO EXCEÇÃO - Copa Jogo de Volta"
            recomendacao_texto = f"Aplicar Handicap Europeu +2 a favor da equipe que administra a vantagem."
            st.info(f"💡 **Mercado Recomendado:** {recomendacao_texto}")
        else:
            st.warning("⚠️ **ATENÇÃO:** Jogo de volta de copa sem vantagem clara. Tratar com extrema cautela.")
            diagnostico_status = "ALERTA - Copa sem vantagem"
            recomendacao_texto = "Entrada reduzida ou aguardar mercado ao vivo (Mina de Ouro)."
    else:
        if xg_partida > 2.0:
            st.error(f"❌ **ALERTA VERMELHO - ALTO RISCO DE GOLEADA!** O xG da partida é de **{xg_partida:.2f}** gols (Superior ao limite estrito de 2.0). Este jogo viola o método de Múltiplas Seguras pré-live!")
            diagnostico_status = "REPROVADO - xG elevado"
            recomendacao_texto = "Evitar handicap pré-live devido ao risco de estouro de gols."
        elif not is_parelho:
            st.warning(f"⚠️ **PARTIDA DESEQUILIBRADA!** A diferença entre as odds é de **{diff_odd:.2f}** (Superior a 1.20). Há um favorito claro, violando a regra dos confrontos parelhos.")
            diagnostico_status = "REPROVADO - Favorito Evidente"
            recomendacao_texto = "O método funciona melhor em partidas parelhas onde a zebra tem odd esticada."
        else:
            st.success("✅ **PARTIDA 100% APROVADA PARA O MÉTODO PRINCIPAL!**")
            diagnostico_status = "APROVADO - Método Principal"
            recomendacao_texto = f"Aplicar **Handicap Europeu +3** a favor do **{maior_odd_time}** (Odd de vitória: {maior_odd_valor:.2f})."
            st.info(f"💡 **Recomendação Pré-Live:** {recomendacao_texto}\n\n*Na prática: A aposta é vencedora mesmo se o {maior_odd_time} perder por até 2 gols de diferença.*")

    # Ações: Salvar Histórico e Copiar para Telegram
    st.markdown("---")
    col_act1, col_act2 = st.columns(2)
    
    match_payload = {
        "time_casa": time_casa,
        "time_visi": time_visi,
        "odd_casa": odd_casa,
        "odd_empate": odd_empate,
        "odd_visi": odd_visi,
        "xg_partida": xg_partida,
        "diagnostico": diagnostico_status,
        "recomendacao": recomendacao_texto,
        "ev_percent": ev_percent
    }

    with col_act1:
        if st.button("💾 Salvar Análise no Histórico Local", use_container_width=True):
            if add_match_to_history(match_payload):
                st.toast("Análise salva com sucesso!", icon="✅")
            else:
                st.error("Erro ao salvar análise.")

    with col_act2:
        texto_export = format_match_analysis(match_payload)
        st.text_area("📋 Texto para Telegram/WhatsApp:", value=texto_export, height=140)
