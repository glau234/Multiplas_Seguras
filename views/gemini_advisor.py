import streamlit as st
from utils.gemini_assistant import (
    chat_with_gemini, 
    generate_ai_ticket_suggestions, 
    call_gemini_api,
    analyze_user_bets_with_gemini
)
from utils.calculations import filter_out_serie_b

def render_gemini_advisor():
    st.title("🤖 Consultor & Auditoria IA - Google Gemini")
    st.markdown("Assistente inteligente alimentado pela IA do Google Gemini. Faça auditorias de suas apostas anteriores para identificar onde está errando, tire dúvidas e receba recomendações estratégicas.")

    gemini_key = st.session_state.get("gemini_api_key", "AQ.Ab8RN6LvNVvx0BfHQbiL-_rYW3LN-DJLGChlDB36yrzkJ4ut-Q")
    packball_matches = filter_out_serie_b(st.session_state.get("packball_matches", []))

    # Barra de Status
    col_stat1, col_stat2, col_stat3 = st.columns([1.5, 1.5, 1])
    with col_stat1:
        st.metric("Confrontos em Memória (IA)", f"{len(packball_matches)} jogos", help="Jogos atualmente extraídos do Packball disponíveis para contexto.")
    with col_stat2:
        status_ia = "🟢 Conectado" if gemini_key else "🔴 Sem Chave"
        st.metric("Status da API Gemini", status_ia)
    with col_stat3:
        if st.button("🗑️ Limpar Sessão IA", use_container_width=True):
            st.session_state["gemini_chat_history"] = []
            st.session_state["bet_audit_result"] = None
            st.rerun()

    st.markdown("---")

    # Abas Principais do Consultor IA
    tab_audit, tab_chat = st.tabs([
        "📊 Auditoria de Apostas & Raio-X de Erros", 
        "💬 Chat Estratégico & Sugestões de Bilhetes"
    ])

    # ----------------------------------------------------
    # ABA 1: AUDITORIA DE APOSTAS
    # ----------------------------------------------------
    with tab_audit:
        st.subheader("🔍 Auditoria de Bilhetes & Diagnóstico de Erros")
        st.markdown(
            "Suba um **print do bilhete** de qualquer casa de aposta (Bet365, Betano, Betfair, etc.) ou cole o texto dos seus jogos. "
            "A IA fará um **raio-X completo**, apontando vícios e erros ocultos, e ensinando como estruturar apostas inteligentes com o **Método Múltiplas Seguras**."
        )

        col_input1, col_input2 = st.columns([1.2, 1])

        with col_input1:
            st.markdown("#### 1. Upload do Bilhete / Histórico")
            uploaded_file = st.file_uploader(
                "Envie o Print do Bilhete ou Histórico de Apostas:",
                type=["png", "jpg", "jpeg", "webp", "txt", "csv", "pdf"],
                help="Você pode enviar uma foto/print da tela da sua casa de aposta com os jogos ou um arquivo de texto/csv."
            )

            if uploaded_file is not None:
                if uploaded_file.type.startswith("image/"):
                    st.image(uploaded_file, caption="📸 Imagem do Bilhete Anexada", use_column_width=True)
                else:
                    st.info(f"📄 Arquivo anexado: **{uploaded_file.name}** ({uploaded_file.size} bytes)")

        with col_input2:
            st.markdown("#### 2. Detalhes ou Texto Adicional (Opcional)")
            
            # Botões de exemplo rápido
            st.caption("💡 Ou teste com um exemplo rápido:")
            col_ex1, col_ex2 = st.columns(2)
            exemplo_texto = ""
            if col_ex1.button("📌 Múltipla com Red", use_container_width=True):
                exemplo_texto = """Bilhete Múltiplo (Betano):
1. Real Madrid vs Osasuna - Vencedor: Real Madrid @1.30 (Deu Empate 1x1 - RED)
2. Manchester City vs Everton - Mais de 2.5 Gols @1.55 (GREEN)
3. Juventus vs Torino - Ambos Marcam: Sim @1.90 (GREEN)
4. Santos vs Coritiba (Série B) - Santos Vence @1.75 (RED)
5. PSG vs Lens - Mais de 9.5 Escanteios @1.85 (RED)
Odd Total: 12.38 | Valor Apostado: R$ 50,00 | Retorno: R$ 0,00"""
                st.session_state["manual_bet_text"] = exemplo_texto
                st.rerun()

            if col_ex2.button("📌 Aposta Simples Arriscada", use_container_width=True):
                exemplo_texto = """Aposta Simples (Bet365):
Arsenal vs Chelsea - Arsenal Vence @1.65
Valor Apostado: R$ 200,00 (40% da minha banca de R$ 500)
Resultado: Empate 2x2 (RED)"""
                st.session_state["manual_bet_text"] = exemplo_texto
                st.rerun()

            manual_text = st.text_area(
                "Cole aqui o resumo das suas apostas / bilhetes:",
                value=st.session_state.get("manual_bet_text", ""),
                placeholder="Exemplo:\nJogo 1: Real Madrid vs Betis - Vitória Real Madrid @1.40 (Red)\nJogo 2: Arsenal vs Chelsea - Mais de 2.5 gols @1.80 (Green)\nOdd Total: 2.52 | Stake: R$ 100",
                height=180,
                key="manual_bet_text_input"
            )
            
            notes = st.text_input(
                "Dúvida ou objetivo específico (opcional):",
                placeholder="Ex: Como eu poderia ter protegido essa múltipla sem perder tudo?",
                key="audit_notes_input"
            )

        st.markdown("---")

        # Botão de Execução da Auditoria
        if st.button("🚀 Auditar Minhas Apostas com o Gemini IA", type="primary", use_container_width=True):
            if not uploaded_file and not manual_text.strip():
                st.error("⚠️ Por favor, envie uma imagem/arquivo do bilhete OU digite o texto das suas apostas para análise.")
            else:
                with st.spinner("🤖 O Google Gemini está lendo os bilhetes, identificando os mercados e calculando o diagnóstico de erros..."):
                    img_bytes = None
                    mime_type = "image/png"
                    file_text = ""

                    if uploaded_file is not None:
                        if uploaded_file.type.startswith("image/"):
                            img_bytes = uploaded_file.getvalue()
                            mime_type = uploaded_file.type
                        else:
                            try:
                                file_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
                            except Exception:
                                file_text = f"Arquivo {uploaded_file.name} carregado."

                    texto_completo = manual_text
                    if file_text:
                        texto_completo = f"{texto_completo}\n\nConteúdo do Arquivo Anexado:\n{file_text}"

                    resultado_auditoria = analyze_user_bets_with_gemini(
                        api_key=gemini_key,
                        bet_text=texto_completo,
                        image_bytes=img_bytes,
                        mime_type=mime_type,
                        additional_notes=notes
                    )

                    st.session_state["bet_audit_result"] = resultado_auditoria

        # Exibição do Resultado da Auditoria
        if st.session_state.get("bet_audit_result"):
            st.markdown("---")
            with st.container(border=True):
                st.markdown("## 🧠 Relatório de Auditoria & Inteligência Estratégica")
                st.markdown(st.session_state["bet_audit_result"])

    # ----------------------------------------------------
    # ABA 2: CHAT ESTRATÉGICO & SUGESTÕES DE BILHETES
    # ----------------------------------------------------
    with tab_chat:
        st.subheader("💬 Chat com Assistente Especialista")
        st.markdown("Converse livremente com a IA sobre jogos, estratégias e gestão de risco.")

        # Ações Rápidas com 1 Clique
        st.markdown("### ⚡ Ações Rápidas com IA")
        col_a1, col_a2, col_a3 = st.columns(3)
        
        with col_a1:
            if st.button("🎫 Sugerir Melhor Bilhete Duplo/Triplo", use_container_width=True):
                if not packball_matches:
                    st.info("Extraia os jogos no painel **🌐 Integração Packball** antes de pedir sugestões de bilhetes.")
                else:
                    with st.spinner("O Gemini está analisando os confrontos e calculando as melhores combinações..."):
                        resposta = generate_ai_ticket_suggestions(packball_matches, gemini_key)
                        if "gemini_chat_history" not in st.session_state:
                            st.session_state["gemini_chat_history"] = []
                        st.session_state["gemini_chat_history"].append({"role": "user", "content": "Sugerir a melhor combinação de bilhete com os jogos extraídos hoje."})
                        st.session_state["gemini_chat_history"].append({"role": "assistant", "content": resposta})
                        st.rerun()

        with col_a2:
            if st.button("🛡️ Avaliar Risco Médio da Rodada", use_container_width=True):
                if not packball_matches:
                    st.info("Extraia os jogos do Packball primeiro.")
                else:
                    with st.spinner("Avaliando médias de ExG, probabilidades e volatilidade..."):
                        prompt = f"Avalie a qualidade geral e o nível de risco da lista de {len(packball_matches)} jogos extraídos hoje. Destaque ligas que estão mais propícias para Handicap +3 e quais evitar."
                        if "gemini_chat_history" not in st.session_state:
                            st.session_state["gemini_chat_history"] = []
                        st.session_state["gemini_chat_history"].append({"role": "user", "content": prompt})
                        resposta = chat_with_gemini(st.session_state["gemini_chat_history"], packball_matches, gemini_key)
                        st.session_state["gemini_chat_history"].append({"role": "assistant", "content": resposta})
                        st.rerun()

        with col_a3:
            if st.button("📖 Explicar Método & Alavancagem", use_container_width=True):
                with st.spinner("Consultando guia metodológico..."):
                    prompt = "Explique detalhadamente como funciona o Método Múltiplas Seguras (Handicap +3, Odds 1.40 a 2.20) e a Estratégia Mina de Ouro (Ao vivo), além da importância de não apostar na Série B brasileira."
                    if "gemini_chat_history" not in st.session_state:
                        st.session_state["gemini_chat_history"] = []
                    st.session_state["gemini_chat_history"].append({"role": "user", "content": prompt})
                    resposta = call_gemini_api(prompt, gemini_key)
                    st.session_state["gemini_chat_history"].append({"role": "assistant", "content": resposta})
                    st.rerun()

        st.markdown("---")

        # Histórico de Mensagens do Chat
        if "gemini_chat_history" not in st.session_state:
            st.session_state["gemini_chat_history"] = [
                {
                    "role": "assistant",
                    "content": "Olá! Sou seu assistente estatístico e auditor de apostas alimentado pelo Google Gemini. Você pode subir bilhetes para análise de erros ou me fazer qualquer pergunta sobre estratégias, partidas e gestão de banca. Como posso ajudar?"
                }
            ]

        for message in st.session_state["gemini_chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Campo de Entrada de Mensagem do Usuário
        if user_prompt := st.chat_input("Digite sua dúvida (ex: 'Quais cuidados devo ter ao apostar em Premier League hoje?'):"):
            st.session_state["gemini_chat_history"].append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                with st.spinner("O Gemini está analisando e formulando a resposta..."):
                    resposta_gemini = chat_with_gemini(
                        st.session_state["gemini_chat_history"],
                        packball_matches,
                        gemini_key
                    )
                    st.markdown(resposta_gemini)

            st.session_state["gemini_chat_history"].append({"role": "assistant", "content": resposta_gemini})
