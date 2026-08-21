import streamlit as st
import numpy as np
from utils.calculations import calculate_total_odd, calculate_stake
from utils.storage import add_ticket_to_history
from utils.exporter import format_ticket_summary

def render_ticket_simulator():
    st.title("📝 Gerador & Simulador de Bilhetes Inteligente")
    st.markdown("Monte bilhetes profissionais aplicando a gestão rígida de banca e alertas de segurança do método.")

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        tipo_bilhete = st.selectbox(
            "Selecione o Tipo do Bilhete:", 
            ["Múltipla Segura (Handicaps)", "Estatísticas Secundárias (Escanteios)"]
        )
    with col_cfg2:
        banca_total = st.number_input(
            "Valor da sua Banca Total (R$):", 
            min_value=10.0, 
            value=100.0, 
            step=10.0
        )

    # Gestão de Stake recomendada
    stake_info = calculate_stake(banca_total, tipo_bilhete)
    valor_aposta = stake_info["stake_value"]
    percent_aposta = stake_info["percent"]
    nivel_risco = stake_info["risk_level"]

    col_stk1, col_stk2 = st.columns(2)
    with col_stk1:
        st.info(f"💡 **Gestão Recomendada:** **{percent_aposta}% da banca** (Nível de Risco: {nivel_risco})")
    with col_stk2:
        st.metric(label="Stake Exata a Apostar", value=f"R$ {valor_aposta:.2f}")

    st.markdown("---")
    st.subheader("⚙️ Seleções do Bilhete")

    jogos_simultaneos = st.checkbox("⚠️ Algumas das seleções ocorrem no mesmo horário/dia?", value=False)
    
    # Importação do Packball
    packball_matches = st.session_state.get("packball_approved_matches", [])
    if packball_matches:
        st.info(f"📥 {len(packball_matches)} jogo(s) aprovado(s) importado(s) da Integração Packball!")
        default_num_jogos = min(len(packball_matches), 10)
    else:
        default_num_jogos = 2

    num_jogos = st.slider("Quantidade de Seleções no Bilhete:", min_value=1, max_value=10, value=default_num_jogos)

    selecoes = []
    odds_lista = []

    cols = st.columns(min(num_jogos, 3))
    for i in range(num_jogos):
        col_idx = i % 3
        
        # Preencher defaults caso exista importação
        def_jogo = f"Jogo {i+1}"
        def_hr = f"Sáb {16+i}:00"
        def_sel = "Handicap +3"
        def_odd = 1.12
        
        if i < len(packball_matches):
            p_match = packball_matches[i]
            def_jogo = p_match.get("jogo", def_jogo)
            def_hr = p_match.get("data", def_hr)
            def_sel = p_match.get("mercado", def_sel)
            def_odd = p_match.get("odd", def_odd)

        with cols[col_idx]:
            st.markdown(f"#### ⚽ Seleção {i+1}")
            jogo = st.text_input(f"Partida {i+1}:", def_jogo, key=f"jg_{i}")
            horario = st.text_input(f"Dia/Horário {i+1}:", def_hr, key=f"hr_{i}")
            selecao_nome = st.text_input(f"Entrada {i+1}:", def_sel, key=f"sl_{i}")
            odd = st.number_input(f"Odd {i+1}:", min_value=1.01, value=float(def_odd), step=0.01, key=f"od_{i}")
            
            odds_lista.append(odd)
            selecoes.append({
                "jogo": jogo,
                "horario": horario,
                "selecao": selecao_nome,
                "odd": odd
            })

    odd_total = calculate_total_odd(odds_lista)
    retorno_bruto = round(valor_aposta * odd_total, 2)
    lucro_liquido = round(retorno_bruto - valor_aposta, 2)

    st.markdown("---")
    st.subheader("📊 Resumo do Bilhete & Alertas de Risco")

    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Odd Total do Bilhete", f"{odd_total:.2f}")
    col_r2.metric("Retorno Bruto Estimado", f"R$ {retorno_bruto:.2f}")
    col_r3.metric("Lucro Líquido Estimado", f"R$ {lucro_liquido:.2f}")

    # Validações e Alertas do Método
    if num_jogos > 3:
        st.error("🚨 **ALERTA DE QUANTIDADE:** Bilhetes com mais de 3 seleções aumentam drasticamente o risco! O método preconiza paciência, qualidade e bilhetes duplos ou triplos no máximo.")
    else:
        st.success("✅ **QUANTIDADE IDEAL:** Bilhete enxuto mantendo alto controle de risco.")

    if jogos_simultaneos:
        st.warning("⚠️ **ALERTA CRONOLÓGICO:** Jogos no mesmo horário impedem a **Gestão Ativa**! O método exige jogos espaçados para permitir Cash Out e alocação sequencial de banca.")
    else:
        st.info("📅 **CRONOGRAMA ESPAÇADO:** Permite gerenciamento ativo entre as partidas.")

    if odd_total < 1.42:
        st.warning(f"⚠️ **ODD ABAIXO DA META:** A Odd Total de **{odd_total:.2f}** está inferior ao valor mínimo sugerido (1.42) para garantir o retorno matemático de longo prazo.")

    # Accão: Salvar & Exportar
    st.markdown("---")
    ticket_payload = {
        "tipo_bilhete": tipo_bilhete,
        "banca_total": banca_total,
        "stake_percent": percent_aposta,
        "stake_valor": valor_aposta,
        "selecoes": selecoes,
        "odd_total": odd_total,
        "retorno_potencial": retorno_bruto,
        "lucro_liquido": lucro_liquido
    }

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Salvar Bilhete no Histórico Local", use_container_width=True):
            if add_ticket_to_history(ticket_payload):
                st.toast("Bilhete salvo com sucesso!", icon="✅")
            else:
                st.error("Erro ao salvar bilhete.")

    with col_btn2:
        texto_export = format_ticket_summary(ticket_payload)
        st.text_area("📋 Texto Formatado para Telegram/WhatsApp:", value=texto_export, height=160)
