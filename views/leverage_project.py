import streamlit as st
import pandas as pd
from utils.calculations import generate_leverage_dataframe
from utils.storage import update_leverage_progress, load_data

def render_leverage_project():
    st.title("📈 Projeto Alavancagem - Juros Compostos")
    st.markdown("Simulador matemático do plano de crescimento sustentável de banca de **R$ 100 a R$ 1 Milhão em 100 etapas**.")

    data_store = load_data()
    leverage_data = data_store.get("leverage_progress", {})
    current_step_saved = leverage_data.get("current_step", 0)

    col_inp1, col_inp2, col_inp3 = st.columns(3)
    with col_inp1:
        banca_inicial = st.number_input("Banca Inicial (R$):", min_value=10.0, value=100.0, step=10.0)
    with col_inp2:
        odd_media = st.number_input("Odd Média por Etapa:", min_value=1.01, value=1.10, step=0.01)
    with col_inp3:
        etapas_totais = st.slider("Total de Etapas:", min_value=10, max_value=100, value=100)

    st.markdown("### 💵 Calculadora de Aportes Mensais Recorrentes")
    col_ap1, col_ap2 = st.columns(2)
    with col_ap1:
        aporte_mensal = st.number_input("Aporte Mensal Recorrente (R$):", min_value=0.0, value=100.0, step=50.0)
    with col_ap2:
        etapas_por_mes = st.number_input("Etapas realizadas por Mês:", min_value=1, value=10, step=1)

    # Gerar DataFrame de projeção
    df_proj = generate_leverage_dataframe(banca_inicial, odd_media, etapas_totais, aporte_mensal, etapas_por_mes)

    st.markdown("---")
    st.subheader("📊 Gráfico de Crescimento Acumulado")
    
    # Gráfico comparativo
    st.line_chart(df_proj.set_index("Etapa")[["Valor Com Aportes (R$)", "Valor Sem Aportes (R$)"]])

    # Metas Visuais Claras
    st.markdown("---")
    st.subheader("🎯 Marcos Globais do Método (Sem Aportes, Odd 1.10)")

    meta_40 = banca_inicial * (odd_media ** 40)
    meta_50 = banca_inicial * (odd_media ** 50)
    meta_100 = banca_inicial * (odd_media ** 100)

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Etapa 40 (Aceleração da Curva)", f"R$ {meta_40:,.2f}")
    col_m2.metric("Etapa 50 (Ponto de Saque 50%)", f"R$ {meta_50:,.2f}")
    col_m3.metric("Etapa 100 (Meta Final)", f"R$ {meta_100:,.2f}")

    st.warning("⚠️ **MOMENTO CRÍTICO NA ETAPA 50:** Ao atingir a Etapa 50 (~R$ 11.739,00), a recomendação rígida do método é **SACAR 50% DO VALOR** para colocar o lucro no bolso e garantir o resultado real. O projeto continua com os 50% restantes sem nenhum risco sobre o capital inicial!")

    # Rastreador de Progresso Real
    st.markdown("---")
    st.subheader("📍 Rastreador do Seu Progresso Atual")

    col_prog1, col_prog2 = st.columns(2)
    with col_prog1:
        etapa_atual = st.number_input("Qual a sua Etapa Atual?", min_value=0, max_value=etapas_totais, value=current_step_saved)
    with col_prog2:
        banca_meta_etapa = banca_inicial * (odd_media ** etapa_atual)
        st.metric(label=f"Banca Teórica Esperada na Etapa {etapa_atual}", value=f"R$ {banca_meta_etapa:,.2f}")

    if st.button("💾 Atualizar Meu Progresso Atual no Histórico", use_container_width=True):
        if update_leverage_progress(etapa_atual, banca_meta_etapa):
            st.toast("Progresso de alavancagem salvo!", icon="🎯")
        else:
            st.error("Erro ao salvar progresso.")

    with st.expander("📄 Visualizar Tabela Completa Etapa por Etapa"):
        st.dataframe(df_proj, use_container_width=True)
