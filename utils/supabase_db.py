import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

def get_supabase_credentials() -> Optional[Dict[str, str]]:
    """
    Retorna a URL e a API Key do Supabase se configuradas via st.secrets ou os.environ.
    """
    url = None
    key = None
    
    # 1. Tenta ler via Streamlit Secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "SUPABASE_URL" in st.secrets:
                url = str(st.secrets["SUPABASE_URL"]).strip()
            if "SUPABASE_KEY" in st.secrets:
                key = str(st.secrets["SUPABASE_KEY"]).strip()
    except Exception:
        pass
        
    # 2. Fallback para Variáveis de Ambiente
    if not url:
        url = os.environ.get("SUPABASE_URL", "").strip()
    if not key:
        key = os.environ.get("SUPABASE_KEY", "").strip()
        
    if url and key and url.startswith("http"):
        return {"url": url.rstrip("/"), "key": key}
        
    return None

def is_supabase_configured() -> bool:
    """Retorna True se o Supabase estiver devidamente configurado."""
    return get_supabase_credentials() is not None

def _supabase_request(endpoint: str, method: str = "GET", payload: Any = None, query_params: str = "") -> Optional[Any]:
    """
    Realiza uma requisição à REST API PostgREST do Supabase sem dependências externas.
    """
    creds = get_supabase_credentials()
    if not creds:
        return None
        
    url = f"{creds['url']}/rest/v1/{endpoint}"
    if query_params:
        url += f"?{query_params}"
        
    headers = {
        "apikey": creds["key"],
        "Authorization": f"Bearer {creds['key']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if method.upper() in ["POST", "PATCH"]:
        headers["Prefer"] = "return=representation,resolution=merge-duplicates"
        
    data_bytes = None
    if payload is not None:
        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method.upper())
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_body = response.read().decode("utf-8")
            if res_body:
                return json.loads(res_body)
            return True
    except Exception as e:
        print(f"Erro na requisição ao Supabase ({method} {endpoint}): {e}")
        return None

# ====================================================
# OPERAÇÕES CRUD DE BILHETES SIMULADOS (PAPER TRADING)
# ====================================================

def sp_get_simulated_tickets() -> Optional[List[Dict[str, Any]]]:
    """Busca todos os bilhetes simulados do Supabase em ordem decrescente."""
    res = _supabase_request("simulated_tickets", method="GET", query_params="select=*&order=created_at.desc")
    if isinstance(res, list):
        return res
    return None

def sp_add_simulated_ticket(ticket: Dict[str, Any]) -> bool:
    """Insere um novo bilhete simulado no Supabase."""
    res = _supabase_request("simulated_tickets", method="POST", payload=ticket)
    return res is not None

def sp_update_simulated_ticket(ticket_id: str, fields: Dict[str, Any]) -> bool:
    """Atualiza o status ou resultado de um bilhete simulado no Supabase."""
    query = f"id=eq.{urllib.parse.quote(str(ticket_id))}"
    res = _supabase_request("simulated_tickets", method="PATCH", payload=fields, query_params=query)
    return res is not None

def sp_delete_simulated_ticket(ticket_id: str) -> bool:
    """Exclui um bilhete simulado no Supabase pelo ID."""
    query = f"id=eq.{urllib.parse.quote(str(ticket_id))}"
    res = _supabase_request("simulated_tickets", method="DELETE", query_params=query)
    return res is not None

def sp_clear_simulated_tickets() -> bool:
    """Limpa a tabela de bilhetes simulados no Supabase."""
    query = "id=neq.none"
    res = _supabase_request("simulated_tickets", method="DELETE", query_params=query)
    return res is not None

# ====================================================
# OPERAÇÕES CRUD DE BILHETES GERADOS (SIMULADOR INTELIGENTE)
# ====================================================

def sp_get_tickets() -> Optional[List[Dict[str, Any]]]:
    """Busca todos os bilhetes gerados salvos no Supabase."""
    res = _supabase_request("tickets", method="GET", query_params="select=*&order=created_at.desc")
    if isinstance(res, list):
        return res
    return None

def sp_add_ticket(ticket: Dict[str, Any]) -> bool:
    """Salva um bilhete gerado no Supabase."""
    import time
    import random
    if "id" not in ticket:
        ticket["id"] = f"t_{int(time.time() * 1000)}_{random.randint(100, 999)}"
    res = _supabase_request("tickets", method="POST", payload=ticket)
def sp_delete_ticket(ticket_id: str) -> bool:
    """Exclui um bilhete do Supabase pelo ID."""
    query = f"id=eq.{urllib.parse.quote(str(ticket_id))}"
    res = _supabase_request("tickets", method="DELETE", query_params=query)
    return res is not None

def sp_clear_tickets() -> bool:
    """Limpa a tabela de bilhetes no Supabase."""
    query = "id=neq.none"
    res = _supabase_request("tickets", method="DELETE", query_params=query)
    return res is not None

# ====================================================
# OPERAÇÕES CRUD DE USUÁRIOS
# ====================================================

def sp_load_users() -> Optional[List[Dict[str, Any]]]:
    """Carrega os usuários cadastrados do Supabase."""
    res = _supabase_request("users", method="GET", query_params="select=*")
    if isinstance(res, list):
        return res
    return None

def sp_save_user(user: Dict[str, Any]) -> bool:
    """Salva ou atualiza um usuário no Supabase."""
    res = _supabase_request("users", method="POST", payload=user)
    return res is not None

def sp_update_user_password(email: str, password_hash: str) -> bool:
    """Atualiza o hash da senha de um usuário no Supabase."""
    query = f"email=eq.{urllib.parse.quote(email.strip().lower())}"
    res = _supabase_request("users", method="PATCH", payload={"password_hash": password_hash}, query_params=query)
    return res is not None

def sp_toggle_user_status(email: str, active: bool) -> bool:
    """Ativa ou desativa um usuário no Supabase."""
    query = f"email=eq.{urllib.parse.quote(email.strip().lower())}"
    res = _supabase_request("users", method="PATCH", payload={"active": active}, query_params=query)
    return res is not None

def sp_delete_user(email: str) -> bool:
    """Exclui um usuário do Supabase."""
    query = f"email=eq.{urllib.parse.quote(email.strip().lower())}"
    res = _supabase_request("users", method="DELETE", query_params=query)
    return res is not None
