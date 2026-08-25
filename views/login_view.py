import streamlit as st
from utils.auth import authenticate_user

def render_login_view():
    """Renderiza a tela de login segura com design moderno e integrado."""
    st.markdown(
        """
        <div style="text-align: center; margin-top: 20px; margin-bottom: 25px;">
            <div style="font-size: 3rem;">⚽🛡️</div>
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #1E293B; margin-bottom: 5px;">Método Múltiplas Seguras</h1>
            <p style="font-size: 1.05rem; color: #64748B; font-weight: 500;">Portal de Acesso Exclusivo & Inteligência IA</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_l1, col_l2, col_l3 = st.columns([1, 1.4, 1])

    with col_l2:
        with st.container(border=True):
            st.markdown("### 🔐 Autenticação de Usuário")
            st.markdown("Insira seu e-mail e senha cadastrados para acessar a plataforma:")

            email_input = st.text_input("📧 E-mail de Acesso:", placeholder="exemplo@gmail.com", key="login_email")
            senha_input = st.text_input("🔑 Senha:", type="password", placeholder="Digite sua senha", key="login_pass")

            col_btn, col_extra = st.columns([1.5, 1])
            with col_btn:
                if st.button("🚀 Entrar no Sistema", type="primary", use_container_width=True):
                    if not email_input or not senha_input:
                        st.error("Por favor, preencha o e-mail e a senha.")
                    else:
                        resultado = authenticate_user(email_input, senha_input)
                        if "error" in resultado:
                            st.error(f"❌ {resultado['error']}")
                        else:
                            st.session_state["authenticated_user"] = resultado
                            st.success(f"Bem-vindo, {resultado.get('name')}!")
                            st.rerun()

            st.markdown("---")
            st.info(
                "👑 **Acesso Inicial do Administrador:**\n\n"
                "• **E-mail:** `glaucio.silva@gmail.com`\n\n"
                "• **Senha Padrão:** `admin123456`\n\n"
                "*(Você pode alterar sua senha e incluir outros usuários a qualquer momento no menu de Admin)*"
            )
