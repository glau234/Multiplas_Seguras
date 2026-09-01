import streamlit as st
from utils.auth import (
    load_users, 
    register_user, 
    delete_user, 
    toggle_user_status, 
    update_user_password
)

def render_admin_management():
    current_user = st.session_state.get("authenticated_user", {})
    if current_user.get("role") != "admin":
        st.error("⛔ Acesso Restrito: Apenas administradores podem gerenciar usuários.")
        return

    st.title("👑 Painel de Administração & Gestão de Usuários")
    st.markdown("Gerencie os acessos à plataforma **Método Múltiplas Seguras**. Você pode cadastrar novos membros, ativar, desativar ou excluir usuários cadastrados.")

    users = load_users()
    total_users = len(users)
    active_users = sum(1 for u in users if u.get("active", True))
    admin_users = sum(1 for u in users if u.get("role") == "admin")

    st.markdown("---")
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total de Usuários", f"{total_users}")
    col_m2.metric("🟢 Usuários Ativos", f"{active_users}")
    col_m3.metric("👑 Administradores", f"{admin_users}")
    st.markdown("---")

    tab_list, tab_add, tab_my_pass = st.tabs([
        f"📋 Usuários Cadastrados ({total_users})", 
        "➕ Cadastrar Novo Usuário", 
        "🔑 Alterar Minha Senha de Admin"
    ])

    # ====================================================
    # ABA 1: LISTA E CONTROLE DE USUÁRIOS
    # ====================================================
    with tab_list:
        st.subheader("📋 Lista de Membros Cadastrados")

        for idx, u in enumerate(users):
            u_name = u.get("name", "Sem Nome")
            u_email = u.get("email", "")
            u_role = u.get("role", "user")
            u_active = u.get("active", True)
            u_created = u.get("created_at", "N/A")

            role_badge = "👑 Administrador" if u_role == "admin" else "👤 Usuário VIP"
            status_badge = "🟢 Ativo" if u_active else "🔴 Desativado"
            status_color = "#059669" if u_active else "#DC2626"

            with st.container(border=True):
                col_u1, col_u2, col_u3 = st.columns([2.5, 1.5, 2])
                with col_u1:
                    st.markdown(f"#### {u_name}")
                    st.caption(f"📧 **{u_email}** &nbsp;|&nbsp; 📅 Cadastrado em: {u_created}")
                with col_u2:
                    st.markdown(f"**Perfil:** `{role_badge}`")
                    st.markdown(f"<span style='color: {status_color}; font-weight: 800;'>Status: {status_badge}</span>", unsafe_allow_html=True)
                
                with col_u3:
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        btn_txt = "🔴 Desativar" if u_active else "🟢 Ativar"
                        if st.button(btn_txt, key=f"tgl_{idx}_{u_email}", use_container_width=True):
                            toggle_user_status(u_email)
                            st.toast(f"Status de {u_name} atualizado!", icon="🔄")
                            st.rerun()

                    with col_btn2:
                        # Previne exclusão da própria conta ativa
                        is_me = (u_email.lower() == current_user.get("email", "").lower())
                        if is_me:
                            st.caption("*(Sua Conta)*")
                        else:
                            if st.button("🗑️ Excluir", key=f"del_{idx}_{u_email}", type="secondary", use_container_width=True):
                                if delete_user(u_email):
                                    st.success(f"Usuário {u_name} excluído!")
                                    st.rerun()
                                else:
                                    st.error("Não foi possível excluir este usuário.")

                    # Redefinir senha
                    with st.expander(f"🔑 Redefinir Senha de {u_name}"):
                        new_p = st.text_input(f"Nova Senha para {u_email}:", type="password", key=f"rst_p_{idx}")
                        if st.button(f"Salvar Nova Senha", key=f"btn_rst_{idx}"):
                            if len(new_p) >= 6:
                                update_user_password(u_email, new_p)
                                st.success("Senha atualizada com sucesso!")
                            else:
                                st.warning("A senha deve conter no mínimo 6 caracteres.")

    # ====================================================
    # ABA 2: CADASTRAR NOVO USUÁRIO
    # ====================================================
    with tab_add:
        st.subheader("➕ Incluir Novo Usuário no Sistema")
        st.markdown("Preencha as informações para liberar o acesso de um novo membro ou administrador:")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            novo_nome = st.text_input("Nome Completo:", placeholder="Ex: Maria Oliveira")
            novo_email = st.text_input("E-mail de Acesso (Google / Pessoal):", placeholder="exemplo@gmail.com")
        with col_f2:
            nova_senha = st.text_input("Senha Inicial de Acesso:", type="password", placeholder="Mínimo 6 caracteres")
            novo_perfil = st.selectbox("Nível de Acesso / Perfil:", ["user", "admin"], format_func=lambda x: "👤 Usuário VIP Padrão" if x == "user" else "👑 Administrador Completo")

        if st.button("✨ Cadastrar Usuário", type="primary", use_container_width=True):
            if not novo_nome or not novo_email or not nova_senha:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            elif len(nova_senha) < 6:
                st.warning("A senha deve ter pelo menos 6 caracteres.")
            elif "@" not in novo_email or "." not in novo_email:
                st.error("Por favor, insira um e-mail válido.")
            else:
                res = register_user(novo_nome, novo_email, nova_senha, novo_perfil)
                if res.get("success"):
                    st.success(f"🎉 {res.get('message')}")
                    st.rerun()
                else:
                    st.error(res.get("message"))

    # ====================================================
    # ABA 3: ALTERAR SENHA DO PRÓPRIO ADMIN
    # ====================================================
    with tab_my_pass:
        st.subheader("🔑 Alterar Minha Senha de Administrador")
        st.markdown(f"Você está conectado como **{current_user.get('name')}** (`{current_user.get('email')}`).")

        senha_atual = st.text_input("Senha Atual:", type="password")
        nova_senha_admin = st.text_input("Nova Senha:", type="password")
        confirma_senha = st.text_input("Confirmar Nova Senha:", type="password")

        if st.button("Atualizar Minha Senha", type="primary", use_container_width=True):
            from utils.auth import authenticate_user
            auth_check = authenticate_user(current_user.get("email"), senha_atual)
            if "error" in auth_check:
                st.error("A senha atual informada está incorreta.")
            elif len(nova_senha_admin) < 6:
                st.warning("A nova senha deve ter no mínimo 6 caracteres.")
            elif nova_senha_admin != confirma_senha:
                st.error("A confirmação de senha não confere.")
            else:
                if update_user_password(current_user.get("email"), nova_senha_admin):
                    st.success("✅ Sua senha de administrador foi atualizada com sucesso!")
                else:
                    st.error("Erro ao atualizar a senha.")
