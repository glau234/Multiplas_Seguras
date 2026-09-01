import os
import json
import hashlib
import time
from typing import Dict, Any, List, Optional

USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")

def hash_password(password: str) -> str:
    """Gera o hash seguro SHA-256 da senha."""
    salt = "multiplas_seguras_secure_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def ensure_users_file():
    """Garante que o arquivo data/users.json exista com o Administrador inicial."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        default_admins = [
            {
                "name": "Glaucio Silveira (Admin)",
                "email": "glaucio.silveira@gmail.com",
                "password_hash": hash_password("admin123456"),
                "role": "admin",
                "active": True,
                "created_at": time.strftime("%d/%m/%Y %H:%M")
            },
            {
                "name": "Glaucio Silva (Admin)",
                "email": "glaucio.silva@gmail.com",
                "password_hash": hash_password("admin123456"),
                "role": "admin",
                "active": True,
                "created_at": time.strftime("%d/%m/%Y %H:%M")
            }
        ]
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_admins, f, ensure_ascii=False, indent=2)

from utils.supabase_db import (
    is_supabase_configured,
    sp_load_users,
    sp_save_user,
    sp_update_user_password,
    sp_toggle_user_status,
    sp_delete_user
)

def load_users() -> List[Dict[str, Any]]:
    """Carrega todos os usuários cadastrados (do Supabase, arquivo JSON local e Streamlit Secrets em produção)."""
    ensure_users_file()
    users = []
    
    # 1. Tenta carregar do Supabase se configurado
    if is_supabase_configured():
        sp_users = sp_load_users()
        if sp_users is not None and len(sp_users) > 0:
            users = sp_users

    # 2. Fallback / Leitura do JSON local se o Supabase não tiver retornado
    if not users:
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    users = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar usuários do JSON: {e}")
            users = []

    # 3. Suporte a credenciais via Streamlit Secrets (st.secrets)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "ADMIN_EMAIL" in st.secrets and "ADMIN_PASSWORD" in st.secrets:
                sec_email = str(st.secrets["ADMIN_EMAIL"]).strip().lower()
                sec_pass = str(st.secrets["ADMIN_PASSWORD"]).strip()
                
                matched = False
                for u in users:
                    if u.get("email", "").strip().lower() == sec_email:
                        u["password_hash"] = hash_password(sec_pass)
                        u["active"] = True
                        matched = True
                        break
                        
                if not matched:
                    users.append({
                        "name": "Administrador (Secrets)",
                        "email": sec_email,
                        "password_hash": hash_password(sec_pass),
                        "role": "admin",
                        "active": True,
                        "created_at": time.strftime("%d/%m/%Y %H:%M")
                    })
                    
            if "USERS" in st.secrets:
                sec_users = st.secrets["USERS"]
                if isinstance(sec_users, list):
                    for su in sec_users:
                        s_email = str(su.get("email", "")).strip().lower()
                        s_pass = str(su.get("password", "")).strip()
                        if s_email and s_pass:
                            matched = False
                            for u in users:
                                if u.get("email", "").strip().lower() == s_email:
                                    u["password_hash"] = hash_password(s_pass)
                                    u["active"] = True
                                    matched = True
                                    break
                            if not matched:
                                users.append({
                                    "name": su.get("name", s_email.split("@")[0]),
                                    "email": s_email,
                                    "password_hash": hash_password(s_pass),
                                    "role": su.get("role", "user"),
                                    "active": True,
                                    "created_at": time.strftime("%d/%m/%Y %H:%M")
                                })
    except Exception as e:
        print(f"Nota: st.secrets não configurado ou indisponível: {e}")

    return users

def save_users(users: List[Dict[str, Any]]) -> bool:
    """Salva a lista de usuários no arquivo JSON."""
    ensure_users_file()
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar usuários: {e}")
        return False

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Autentica o usuário pelo e-mail e senha digitados."""
    users = load_users()
    email_clean = email.strip().lower()
    pass_hash = hash_password(password.strip())

    for u in users:
        if u.get("email", "").strip().lower() == email_clean:
            if u.get("password_hash") == pass_hash:
                if not u.get("active", True):
                    return {"error": "Usuário desativado. Contate o administrador."}
                return u
            else:
                return {"error": "Senha incorreta."}
                
    return {"error": "E-mail não cadastrado no sistema."}

def register_user(name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
    """Cadastra um novo usuário no sistema."""
    users = load_users()
    email_clean = email.strip().lower()

    for u in users:
        if u.get("email", "").strip().lower() == email_clean:
            return {"success": False, "message": f"O e-mail '{email_clean}' já está cadastrado."}

    novo_usuario = {
        "name": name.strip(),
        "email": email_clean,
        "password_hash": hash_password(password.strip()),
        "role": role,
        "active": True,
        "created_at": time.strftime("%d/%m/%Y %H:%M")
    }

    if is_supabase_configured():
        sp_save_user(novo_usuario)

    users.append(novo_usuario)
    if save_users(users):
        return {"success": True, "message": f"Usuário '{name}' cadastrado com sucesso!"}
    return {"success": False, "message": "Erro ao salvar no banco de dados."}

def delete_user(email: str) -> bool:
    """Exclui um usuário pelo e-mail."""
    users = load_users()
    email_clean = email.strip().lower()
    
    admins = [u for u in users if u.get("role") == "admin" and u.get("active", True)]
    user_to_del = next((u for u in users if u.get("email", "").strip().lower() == email_clean), None)
    
    if user_to_del and user_to_del.get("role") == "admin" and len(admins) <= 1:
        return False

    if is_supabase_configured():
        sp_delete_user(email_clean)

    users = [u for u in users if u.get("email", "").strip().lower() != email_clean]
    return save_users(users)

def toggle_user_status(email: str) -> bool:
    """Ativa ou desativa um usuário."""
    users = load_users()
    email_clean = email.strip().lower()
    for u in users:
        if u.get("email", "").strip().lower() == email_clean:
            new_status = not u.get("active", True)
            u["active"] = new_status
            if is_supabase_configured():
                sp_toggle_user_status(email_clean, new_status)
            return save_users(users)
    return False

def update_user_password(email: str, new_password: str) -> bool:
    """Atualiza a senha de um usuário."""
    users = load_users()
    email_clean = email.strip().lower()
    new_hash = hash_password(new_password.strip())
    for u in users:
        if u.get("email", "").strip().lower() == email_clean:
            u["password_hash"] = new_hash
            if is_supabase_configured():
                sp_update_user_password(email_clean, new_hash)
            return save_users(users)
    return False
