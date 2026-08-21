import streamlit as st
import time
from utils.packball_scraper import fetch_packball_matches
from utils.calculations import calculate_xg_and_defense

def render_packball_integration():
    st.title("🌐 Integração Packball VIP - Estatísticas Oficiais")
    st.markdown("Extração oficial dos próximos 7 dias do Packball para assinantes VIP. Dados nativos de **ExG (Expectativa de Gols)**, **Ambas Marcam (BTS %)**, **PPG**, **Probabilidade de Vitória** e **Poder Defensivo**.")

    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔑 Credenciais Packball VIP")
        username = st.text_input("Usuário / Email:", placeholder="seu_email@exemplo.com", value="glaucio.silveira@gmail.com")
        password = st.text_input("Senha:", type="password", value="Denise23")
        
        st.markdown("#### 🎯 Filtros Estatísticos (Packball Nativo)")
        filtro_max_exg = st.slider("ExG Máximo da Partida (Packball):", min_value=1.50, max_value=4.50, value=3.20, step=0.1, help="Partidas com menor ExG favorecem o Handicap +3 e mercados Under.")
        filtro_max_diff = st.slider("Diferença Máxima de Odds (Equilíbrio):", min_value=0.50, max_value=3.50, value=2.50, step=0.1, help="Garante que as partidas sejam parelhas e equilibradas.")
        
        if st.button("🚀 Iniciar Extração Oficial VIP (7 Dias)", use_container_width=True):
            if not username or not password:
                st.error("Por favor, insira o usuário e a senha do Packball.")
            else:
                with st.spinner("Conectando à sua conta VIP do Packball e extraindo métricas oficiais..."):
                    raw_matches = fetch_packball_matches(username, password)
                    
                    if raw_matches and isinstance(raw_matches, dict) and "error" in raw_matches:
                        st.error(raw_matches.get("error", "Erro desconhecido ao extrair dados."))
                    elif raw_matches:
                        # Enriquecer com métricas de defesa calculadas sobre os dados reais
                        enriched_matches = []
                        for m in raw_matches:
                            stats = calculate_xg_and_defense(m.get("odd_casa", 2.0), m.get("odd_empate", 3.10), m.get("odd_visi", 2.0))
                            enriched_match = dict(m)
                            enriched_match.update(stats)
                            # Se o Packball trouxe ExG nativo, damos prioridade a ele
                            if "exg" in m and m["exg"]:
                                enriched_match["exg_oficial"] = m["exg"]
                            else:
                                enriched_match["exg_oficial"] = stats["xg_total"]
                            enriched_matches.append(enriched_match)
                            
                        st.session_state["packball_matches"] = enriched_matches
                        st.success(f"✅ {len(enriched_matches)} partidas VIP extraídas com sucesso direto do Packball!")
                    else:
                        st.warning("Nenhum jogo encontrado que atenda aos critérios.")

    with col2:
        st.subheader("📊 Painel de Confrontos & Métricas VIP")
        
        if "packball_matches" in st.session_state:
            matches = st.session_state["packball_matches"]
            
            if not matches:
                st.info("Nenhuma partida encontrada.")
            else:
                # Aplicar filtros
                aprovados = []
                for m in matches:
                    odd_c = m.get("odd_casa", 1.0)
                    odd_v = m.get("odd_visi", 1.0)
                    exg_val = float(m.get("exg_oficial", m.get("exg", 2.5)))
                    
                    diff_odd = abs(odd_c - odd_v)
                    is_aprovado = (diff_odd <= filtro_max_diff) and (exg_val <= filtro_max_exg)
                    if is_aprovado:
                        aprovados.append(m)
                
                st.write(f"Exibindo **{len(aprovados)}** partidas aprovadas de um total de **{len(matches)}** confrontos VIP.")
                
                for idx, match in enumerate(matches):
                    odd_casa = match.get("odd_casa", 2.0)
                    odd_empate = match.get("odd_empate", 3.10)
                    odd_visi = match.get("odd_visi", 2.0)
                    exg_oficial = match.get("exg_oficial", match.get("exg", 2.5))
                    gols_avg = match.get("gols_avg", "")
                    win_prob = match.get("win_prob", "N/A")
                    ppg = match.get("ppg", "N/A")
                    bts = match.get("bts", "N/A")
                    escanteios_avg = match.get("escanteios_avg", match.get("corners", "N/A"))
                    escanteios_exc = match.get("escanteios_exc", "")
                    pais = match.get("pais", "")
                    liga = match.get("liga", "")
                    horario = match.get("horario", "")
                    data_str = match.get("data", "Hoje")
                    
                    def_casa = match.get("poder_def_casa", 65)
                    def_visi = match.get("poder_def_visi", 65)
                    
                    diff_odd = abs(odd_casa - odd_visi)
                    is_match_aprovado = (diff_odd <= filtro_max_diff) and (float(exg_oficial) <= filtro_max_exg)
                    
                    status_icon = "🟢" if is_match_aprovado else "⚪"
                    maior_odd_time = match['time_casa'] if odd_casa > odd_visi else match['time_visi']
                    
                    exc_display = escanteios_exc if escanteios_exc else escanteios_avg
                    header_title = f"{status_icon} [{data_str}] {match['time_casa']} vs {match['time_visi']} | ExG: {exg_oficial} | Cantos: {escanteios_avg} (ExC: {exc_display}) | {liga} ({pais})"
                    
                    with st.expander(header_title):
                        c1, c2, c3 = st.columns(3)
                        c1.metric(f"Odd {match['time_casa']}", f"{odd_casa:.2f}")
                        c2.metric("Odd Empate", f"{odd_empate:.2f}")
                        c3.metric(f"Odd {match['time_visi']}", f"{odd_visi:.2f}")
                        
                        st.markdown("---")
                        st.markdown("#### 📈 Estatísticas Nativas do Packball")
                        
                        col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
                        col_v1.metric("ExG (Packball)", f"{exg_oficial} gols", help="Expectativa de gols calculada pelo Packball.")
                        col_v2.metric("Ambas Marcam (BTS)", f"{bts}", help="Probabilidade de Ambas as Equipes Marcarem.")
                        col_v3.metric("Prob. Vitória (%)", f"{win_prob}", help="Chance percentual de vitória Casa vs Visitante.")
                        col_v4.metric("Cantos Médios (AVG)", f"{escanteios_avg}", help="Média de escanteios das equipes no Packball.")
                        col_v5.metric("Expect. Cantos (ExC)", f"{exc_display}", help="Expectativa oficial de escanteios da partida.")
                        
                        st.markdown("#### 🛡️ Poder Defensivo das Equipes")
                        col_d1, col_d2 = st.columns(2)
                        col_d1.metric(f"Solidez Defensiva ({match['time_casa']})", f"{def_casa}%", help="Capacidade da defesa de conter o ataque adversário.")
                        col_d2.metric(f"Solidez Defensiva ({match['time_visi']})", f"{def_visi}%", help="Capacidade da defesa de conter o ataque adversário.")
                        
                        if ppg and ppg != "N/A":
                            st.caption(f"🏆 **PPG (Pontos por Jogo):** {match['time_casa']} ({ppg.split('-')[0].strip() if '-' in ppg else ppg}) vs {match['time_visi']} ({ppg.split('-')[1].strip() if '-' in ppg else ''}) | Horário: {horario} | Média Gols (AVG): {gols_avg}")
                        
                        st.info(f"💡 **Recomendação Múltiplas Seguras:** Entrada em **Handicap Europeu +3 ({maior_odd_time})**.")

                if len(aprovados) > 0:
                    st.markdown("---")
                    if st.button(f"➕ Enviar {len(aprovados)} Aprovados para Simulador de Bilhetes", use_container_width=True):
                        transformed_aprovados = []
                        for m in aprovados:
                            maior_odd_time = m['time_casa'] if m.get('odd_casa', 1.0) > m.get('odd_visi', 1.0) else m['time_visi']
                            transformed_aprovados.append({
                                "id": m.get("id", str(time.time())),
                                "jogo": f"{m['time_casa']} vs {m['time_visi']}",
                                "mercado": f"Handicap Europeu +3 ({maior_odd_time})",
                                "odd": 1.15,
                                "status": "Pendente",
                                "data": m.get("data", "Hoje")
                            })
                            
                        st.session_state["packball_approved_matches"] = transformed_aprovados
                        st.success(f"✅ {len(aprovados)} partidas enviadas para o Simulador com sucesso!")
        else:
            st.info("Preencha suas credenciais VIP e inicie a extração para visualizar todos os dados nativos do Packball.")
