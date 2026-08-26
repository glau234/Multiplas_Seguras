import streamlit as st
import time
import random
from utils.storage import (
    get_simulated_tickets, 
    add_simulated_ticket, 
    update_simulated_ticket, 
    delete_simulated_ticket, 
    clear_simulated_tickets
)
from utils.gemini_assistant import (
    parse_pasted_bet_ticket, 
    verify_simulated_ticket_results,
    analyze_match_with_gemini,
    get_api_key
)
from utils.odds_comparator import compare_ticket_bookmakers
from utils.supabase_db import is_supabase_configured

def render_paper_trading():
    st.title("🧪 Simulador Virtual de Apostas (Paper Trading)")
    st.markdown(
        "Teste estratégias em tempo real **sem arriscar dinheiro real**. Monte bilhetes com as odds oficiais do Packball, "
        "defina Stakes simuladas e acompanhe a evolução do seu ROI e Green Rate."
    )

    if is_supabase_configured():
        st.success("🟢 **Banco de Dados:** Conectado ao Supabase (Persistência Permanente na Nuvem Ativa)")
    else:
        st.info("ℹ️ **Banco de Dados:** Modo Local / Fallback (Configure SUPABASE_URL e SUPABASE_KEY no Secrets do Streamlit Cloud para gravar na nuvem)")

    gemini_key = st.session_state.get("gemini_api_key") or get_api_key()
    simulated_tickets = get_simulated_tickets()

    # Métricas Globais da Carteira Simulada
    total_bilhetes = len(simulated_tickets)
    greens = sum(1 for t in simulated_tickets if t.get("status") == "GREEN")
    reds = sum(1 for t in simulated_tickets if t.get("status") == "RED")
    pendentes = sum(1 for t in simulated_tickets if t.get("status", "PENDENTE") == "PENDENTE")
    
    total_investido = sum(float(t.get("stake_valor", 0)) for t in simulated_tickets if t.get("status") in ["GREEN", "RED"])
    lucro_acumulado = sum(float(t.get("lucro_real", 0)) for t in simulated_tickets if t.get("status") in ["GREEN", "RED"])
    
    taxa_acerto = round((greens / (greens + reds) * 100), 1) if (greens + reds) > 0 else 0.0
    roi = round((lucro_acumulado / total_investido * 100), 1) if total_investido > 0 else 0.0

    st.markdown("---")
    col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)
    col_g1.metric("Bilhetes Simulados", f"{total_bilhetes}")
    col_g2.metric("🟢 Greens / 🔴 Reds", f"{greens}G / {reds}R")
    col_g3.metric("⏳ Pendentes", f"{pendentes}")
    col_g4.metric("Lucro Hipotético", f"R$ {lucro_acumulado:.2f}", delta=f"{roi}% ROI" if total_investido > 0 else None)
    col_g5.metric("Taxa de Acerto", f"{taxa_acerto}%")

    st.markdown("---")

    tab_create, tab_monitor = st.tabs([
        "➕ Criar / Colar Novo Bilhete Simulado", 
        f"📋 Meus Bilhetes Salvos ({total_bilhetes})"
    ])

    # ====================================================
    # ABA 1: CRIAR OU COLAR BILHETE SIMULADO
    # ====================================================
    with tab_create:
        st.subheader("📝 Configuração do Bilhete Simulado")
        
        modo_criacao = st.radio(
            "Como deseja criar o bilhete?",
            [
                "📌 Usar Jogos Sugeridos pelo Packball / Gemini",
                "📋 Colar Texto de Bilhete (Bet365 / Betano / Outras)",
                "✍️ Montar Manualmente (Quantos jogos quiser)"
            ],
            horizontal=True
        )

        col_stk1, col_stk2 = st.columns(2)
        with col_stk1:
            stake_simulada = st.number_input(
                "💰 Valor Fictício para Simular (R$):",
                min_value=5.0,
                value=50.0,
                step=10.0,
                help="Defina o valor fictício que você teria apostado nesta entrada."
            )
        with col_stk2:
            nome_bilhete = st.text_input(
                "🏷️ Nome/Identificador do Bilhete (opcional):",
                value=f"Simulação #{total_bilhetes + 1}",
                placeholder="Ex: Dupla Segura La Liga + Brasileirão"
            )

        selecoes_preparadas = []

        # OPÇÃO A: JOGOS SUGERIDOS
        if modo_criacao == "📌 Usar Jogos Sugeridos pelo Packball / Gemini":
            packball_approved = st.session_state.get("packball_approved_matches", [])
            if not packball_approved:
                st.info("💡 Nenhum jogo aprovado no Packball no momento. Você pode extrair jogos no painel **🌐 Integração Packball** ou usar outra opção abaixo.")
                # Exemplo padrão
                selecoes_preparadas = [
                    {"jogo": "Real Betis vs Real Sociedad", "mercado": "Handicap Europeu +3 (Real Sociedad)", "odd": 1.15, "data": "Hoje"},
                    {"jogo": "Valencia vs Sevilla", "mercado": "Handicap Europeu +3 (Sevilla)", "odd": 1.16, "data": "Hoje"}
                ]
            else:
                st.success(f"📥 {len(packball_approved)} jogo(s) carregados da Integração Packball!")
                for m in packball_approved:
                    selecoes_preparadas.append({
                        "jogo": m.get("jogo", "Confronto"),
                        "mercado": m.get("mercado", "Handicap Europeu +3"),
                        "odd": float(m.get("odd", 1.15)),
                        "data": m.get("data", "Hoje")
                    })

        # OPÇÃO B: COLAR TEXTO DE BILHETE
        elif modo_criacao == "📋 Colar Texto de Bilhete (Bet365 / Betano / Outras)":
            st.markdown("Cole o texto copiado de qualquer bilhete de casa de apostas. O Gemini extrairá os jogos e odds automaticamente:")
            texto_colado = st.text_area(
                "Texto do Bilhete:",
                placeholder="Exemplo:\n1. Flamengo x Botafogo - Handicap +3 @1.18\n2. Palmeiras x Santos - Over 1.5 Gols @1.30\n3. Real Madrid x Betis - Real Madrid Vence @1.40",
                height=130
            )
            if st.button("✨ Extrair Seleções com IA", use_container_width=True):
                if texto_colado.strip():
                    with st.spinner("O Gemini está interpretando o texto do bilhete..."):
                        extraidos = parse_pasted_bet_ticket(texto_colado, gemini_key)
                        if extraidos:
                            st.session_state["pasted_parsed_ticket"] = extraidos
                            st.success(f"✅ {len(extraidos)} seleções identificadas com sucesso!")
                        else:
                            st.warning("Não foi possível extrair automaticamente. Você pode preencher manualmente abaixo.")
            
            selecoes_preparadas = st.session_state.get("pasted_parsed_ticket", [
                {"jogo": "Flamengo vs Botafogo", "mercado": "Handicap Europeu +3", "odd": 1.18, "data": "Hoje"},
                {"jogo": "Real Madrid vs Betis", "mercado": "Handicap Europeu +3", "odd": 1.14, "data": "Hoje"}
            ])

        # OPÇÃO C: MONTAR MANUALMENTE
        else:
            qtd_jogos = st.slider("Quantidade de Seleções no Bilhete:", min_value=1, max_value=15, value=3)
            cols = st.columns(min(qtd_jogos, 3))
            for i in range(qtd_jogos):
                with cols[i % 3]:
                    st.markdown(f"#### ⚽ Seleção {i+1}")
                    jg = st.text_input(f"Partida {i+1}:", f"Time A vs Time B {i+1}", key=f"sim_jg_{i}")
                    mc = st.text_input(f"Mercado {i+1}:", "Handicap Europeu +3", key=f"sim_mc_{i}")
                    od = st.number_input(f"Odd {i+1}:", min_value=1.01, value=1.15, step=0.01, key=f"sim_od_{i}")
                    selecoes_preparadas.append({"jogo": jg, "mercado": mc, "odd": od, "data": "Hoje"})

        st.markdown("---")

        # Exibição e Cálculo da Simulação
        if selecoes_preparadas:
            st.markdown("### 🔍 Resumo das Seleções para a Simulação:")
            
            odd_acumulada = 1.0
            for idx, s in enumerate(selecoes_preparadas, start=1):
                odd_acumulada *= float(s.get("odd", 1.0))
                st.write(f"**{idx}. {s.get('jogo')}** — Mercado: `{s.get('mercado')}` | Odd: **@{float(s.get('odd', 1.0)):.2f}**")

            odd_acumulada = round(odd_acumulada, 2)
            retorno_estimado = round(stake_simulada * odd_acumulada, 2)
            lucro_estimado = round(retorno_estimado - stake_simulada, 2)

            st.markdown("---")
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("Odd Total do Bilhete", f"@{odd_acumulada:.2f}")
            col_res2.metric("Retorno Bruto Hipotético", f"R$ {retorno_estimado:.2f}")
            col_res3.metric("Lucro Líquido Hipotético", f"R$ {lucro_estimado:.2f}", delta=f"+{lucro_estimado:.2f}" if lucro_estimado > 0 else None)

            # Comparador Bet365 vs Betano para o Bilhete Simulado
            comp_casas = compare_ticket_bookmakers(selecoes_preparadas)
            if comp_casas:
                st.markdown(
                    f"""
                    <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 10px; margin: 12px 0;">
                        <span style="font-weight: 700; color: #166534;">⚖️ Comparativo de Casas:</span> 
                        Na <b>Bet365</b> pagaria <b>@{comp_casas['odd_total_bet365']} (R$ {round(stake_simulada*comp_casas['odd_total_bet365'], 2):.2f})</b> vs 
                        Na <b>Betano</b> pagaria <b>@{comp_casas['odd_total_betano']} (R$ {round(stake_simulada*comp_casas['odd_total_betano'], 2):.2f})</b>. 
                        Melhor: <b>{comp_casas['melhor_casa']} (+{comp_casas['vantagem_pct']}%)</b>.
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

            if st.button("💾 Salvar Bilhete para Monitoramento & Verificação Futura", type="primary", use_container_width=True):
                novo_bilhete = {
                    "id": f"sim_{int(time.time())}_{random.randint(100, 999)}",
                    "nome": nome_bilhete,
                    "stake_valor": stake_simulada,
                    "odd_total": odd_acumulada,
                    "retorno_potencial": retorno_estimado,
                    "lucro_potencial": lucro_estimado,
                    "selecoes": selecoes_preparadas,
                    "status": "PENDENTE",
                    "data_criacao": time.strftime("%d/%m/%Y %H:%M"),
                    "lucro_real": 0.0,
                    "retorno_real": 0.0,
                    "resultado_detalhado": None
                }
                if add_simulated_ticket(novo_bilhete):
                    st.success("✅ Bilhete simulado salvo com sucesso! Você pode acompanhar e verificar o resultado na aba ao lado.")
                    st.rerun()

    # ====================================================
    # ABA 2: MONITOR DE BILHETES SALVOS & VERIFICAÇÃO DE RESULTADOS
    # ====================================================
    with tab_monitor:
        st.subheader("📋 Meus Bilhetes Simulados")
        
        if not simulated_tickets:
            st.info("Nenhum bilhete simulado salvo no momento. Crie uma simulação na aba ao lado para começar o acompanhamento!")
        else:
            col_act1, col_act2 = st.columns([2, 1])
            with col_act1:
                st.markdown(f"Você possui **{len(simulated_tickets)} bilhetes** na sua carteira de Paper Trading.")
            with col_act2:
                if st.button("🗑️ Limpar Todos os Bilhetes", use_container_width=True):
                    clear_simulated_tickets()
                    st.rerun()

            st.markdown("---")

            for t in simulated_tickets:
                t_id = t.get("id")
                t_nome = t.get("nome", "Bilhete Simulado")
                t_status = t.get("status", "PENDENTE")
                t_stake = float(t.get("stake_valor", 0.0))
                t_odd = float(t.get("odd_total", 1.0))
                t_data = t.get("data_criacao", "")
                t_lucro = float(t.get("lucro_real", t.get("lucro_potencial", 0.0)))

                # Cores de status
                if t_status == "GREEN":
                    badge = "🟢 GREEN (Ganho)"
                    b_color = "#059669"
                elif t_status == "RED":
                    badge = "🔴 RED (Perdido)"
                    b_color = "#DC2626"
                else:
                    badge = "⏳ PENDENTE / EM ANDAMENTO"
                    b_color = "#D97706"

                with st.container(border=True):
                    col_th1, col_th2 = st.columns([3, 1])
                    with col_th1:
                        st.markdown(f"#### 🎫 {t_nome}")
                        st.caption(f"📅 Criado em: {t_data} &nbsp;|&nbsp; Stake Simulada: **R$ {t_stake:.2f}** &nbsp;|&nbsp; Odd Total: **@{t_odd:.2f}**")
                    with col_th2:
                        st.markdown(f"<div style='text-align: right; font-weight: 800; color: {b_color}; font-size: 1rem;'>{badge}</div>", unsafe_allow_html=True)
                        if t_status in ["GREEN", "RED"]:
                            st.markdown(f"<div style='text-align: right; font-weight: 700; color: {b_color}; font-size: 0.9rem;'>Resultado: R$ {t_lucro:+.2f}</div>", unsafe_allow_html=True)

                    # Detalhes das seleções
                    with st.expander("🔍 Ver Seleções Deste Bilhete:", expanded=(t_status == "PENDENTE")):
                        for idx_s, s in enumerate(t.get("selecoes", []), start=1):
                            placar = s.get("placar_final", "")
                            st_sel = s.get("status_selecao", "")
                            status_txt = f"[{st_sel} - {placar}]" if placar else ""
                            st.write(f"**{idx_s}. {s.get('jogo')}** — `{s.get('mercado')}` @{s.get('odd')} {status_txt}")

                        if t.get("resultado_detalhado"):
                            st.info(f"🧠 **Parecer da Verificação:** {t['resultado_detalhado'].get('resumo_analise', '')}")

                    # Botões de Ação para o Bilhete
                    col_b_act1, col_b_act2 = st.columns(2)
                    with col_b_act1:
                        if st.button(f"🏁 Verificar Resultado com Gemini IA", key=f"btn_check_{t_id}", use_container_width=True):
                            with st.spinner("O Gemini está consultando os placares das partidas e calculando o desfecho do bilhete..."):
                                resultado_verificacao = verify_simulated_ticket_results(t, gemini_key)
                                
                                update_simulated_ticket(t_id, {
                                    "status": resultado_verificacao.get("status_geral", "GREEN"),
                                    "retorno_real": resultado_verificacao.get("retorno_real", 0.0),
                                    "lucro_real": resultado_verificacao.get("lucro_real", 0.0),
                                    "resultado_detalhado": resultado_verificacao,
                                    "selecoes": resultado_verificacao.get("itens_verificados", t.get("selecoes", []))
                                })
                                st.success("✅ Resultados verificados com sucesso!")
                                st.rerun()

                    with col_b_act2:
                        if st.button(f"🗑️ Excluir Bilhete", key=f"btn_del_{t_id}", use_container_width=True):
                            delete_simulated_ticket(t_id)
                            st.rerun()
