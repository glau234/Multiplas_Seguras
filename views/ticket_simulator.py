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
    
    # Importação do Packball e Gestão de Jogos no Bilhete
    packball_matches = st.session_state.get("packball_approved_matches", [])
    
    if packball_matches:
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.info(f"📥 **{len(packball_matches)} jogo(s)** no bilhete simulado!")
        with col_hdr2:
            if st.button("🗑️ Limpar Bilhete", key="btn_clear_all_ticket", use_container_width=True):
                st.session_state["packball_approved_matches"] = []
                st.toast("Todos os jogos foram removidos do bilhete.", icon="🗑️")
                st.rerun()
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
            
            d_val = str(p_match.get("data", "")).strip()
            h_val = str(p_match.get("horario", "")).strip()
            if h_val and h_val not in d_val:
                def_hr = f"{d_val} {h_val}".strip() if d_val else h_val
            else:
                def_hr = d_val if d_val else def_hr

            def_sel = p_match.get("mercado", def_sel)
            def_odd = p_match.get("odd", def_odd)

        with cols[col_idx]:
            with st.container(border=True):
                c_sel_t, c_sel_del = st.columns([3, 1])
                with c_sel_t:
                    st.markdown(f"#### ⚽ Seleção {i+1}")
                with c_sel_del:
                    if st.button("🗑️", key=f"btn_del_match_{i}", help=f"Remover esta Seleção {i+1} do bilhete"):
                        if "packball_approved_matches" in st.session_state and i < len(st.session_state["packball_approved_matches"]):
                            removed = st.session_state["packball_approved_matches"].pop(i)
                            st.toast(f"Removido: {removed.get('jogo', 'Jogo')}", icon="🗑️")
                        else:
                            st.toast(f"Seleção {i+1} removida.", icon="🗑️")
                        st.rerun()

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

    from utils.odds_comparator import compare_ticket_bookmakers
    ticket_comp = compare_ticket_bookmakers(selecoes)
    
    if ticket_comp:
        st.markdown("---")
        st.subheader("⚖️ Comparativo de Pagamento: Bet365 vs Betano")
        
        col_tb1, col_tb2, col_tb3 = st.columns([1.2, 1.2, 1.6])
        ret_365 = round(valor_aposta * ticket_comp["odd_total_bet365"], 2)
        ret_betano = round(valor_aposta * ticket_comp["odd_total_betano"], 2)
        
        with col_tb1:
            st.markdown(
                f"""
                <div style="border: 2px solid #059669; border-radius: 12px; padding: 12px; background: #ECFDF5; text-align: center;">
                    <div style="font-weight: 800; color: #047857;">🟢 Bet365 Brasil</div>
                    <div style="font-size: 1.5rem; font-weight: 900; color: #065F46;">Odd @{ticket_comp['odd_total_bet365']:.2f}</div>
                    <div style="font-size: 0.85rem; color: #047857; margin-bottom: 6px;">Retorno: R$ {ret_365:.2f}</div>
                    <a href="https://www.bet365.bet.br/" target="_blank" style="background: #059669; color: white; padding: 5px 12px; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.8rem; display: inline-block;">Apostar na Bet365 ↗</a>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_tb2:
            st.markdown(
                f"""
                <div style="border: 2px solid #EA580C; border-radius: 12px; padding: 12px; background: #FFF7ED; text-align: center;">
                    <div style="font-weight: 800; color: #C2410C;">🟠 Betano Brasil</div>
                    <div style="font-size: 1.5rem; font-weight: 900; color: #9A3412;">Odd @{ticket_comp['odd_total_betano']:.2f}</div>
                    <div style="font-size: 0.85rem; color: #C2410C; margin-bottom: 6px;">Retorno: R$ {ret_betano:.2f}</div>
                    <a href="https://www.betano.bet.br/" target="_blank" style="background: #EA580C; color: white; padding: 5px 12px; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.8rem; display: inline-block;">Apostar na Betano ↗</a>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_tb3:
            winner_color = "#047857" if ticket_comp['melhor_casa'] == "Bet365" else "#EA580C"
            st.markdown(
                f"""
                <div style="border: 1px solid #CBD5E1; border-radius: 12px; padding: 12px; background: #FFFFFF; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                    <div style="font-size: 0.85rem; color: #64748B; font-weight: 700;">🏆 Casa Recomendada para este Bilhete:</div>
                    <div style="font-size: 1.3rem; font-weight: 900; color: {winner_color}; margin: 2px 0;">{ticket_comp['melhor_casa']} (+{ticket_comp['vantagem_pct']}%)</div>
                    <div style="font-size: 0.82rem; color: #334155;">Esta casa paga mais para esta combinação exata de jogos.</div>
                    <div style="margin-top: 6px;">
                        <a href="{ticket_comp['link_vencedor']}" target="_blank" style="font-size: 0.85rem; font-weight: 700; color: {winner_color}; text-decoration: underline;">Abrir {ticket_comp['melhor_casa']} ↗</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Ação: Salvar & Exportar
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
