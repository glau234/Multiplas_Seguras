import json
import os
from typing import Dict, Any, List
from utils.supabase_db import (
    is_supabase_configured,
    sp_get_simulated_tickets,
    sp_add_simulated_ticket,
    sp_update_simulated_ticket,
    sp_delete_simulated_ticket,
    sp_clear_simulated_tickets,
    sp_add_ticket,
    sp_get_tickets,
    sp_delete_ticket,
    sp_clear_tickets
)

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "history.json")

def ensure_data_file():
    """Garante que a pasta data e o arquivo history.json existam com uma estrutura válida."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "matches": [],
            "tickets": [],
            "leverage_progress": {
                "current_step": 0,
                "current_bankroll": 100.0,
                "target_bankroll": 1378061.0,
                "history": []
            },
            "live_signals": [],
            "simulated_tickets": []
        }
        save_data(initial_data)

def load_data() -> Dict[str, Any]:
    """Carrega todos os dados armazenados no arquivo JSON e sincroniza com o Supabase se configurado."""
    ensure_data_file()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Erro ao ler histórico JSON: {e}")
        data = {
            "matches": [],
            "tickets": [],
            "leverage_progress": {"current_step": 0, "current_bankroll": 100.0, "target_bankroll": 1378061.0, "history": []},
            "live_signals": [],
            "simulated_tickets": []
        }

    # Sincroniza em tempo real com o Supabase se estiver conectado
    if is_supabase_configured():
        try:
            sp_sim = sp_get_simulated_tickets()
            if sp_sim is not None:
                data["simulated_tickets"] = sp_sim
            sp_t = sp_get_tickets()
            if sp_t is not None:
                data["tickets"] = sp_t
        except Exception as err:
            print(f"Aviso ao sincronizar Supabase em load_data: {err}")

    return data

def save_data(data: Dict[str, Any]) -> bool:
    """Salva os dados no arquivo JSON local."""
    ensure_data_file()
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar histórico JSON: {e}")
        return False

def add_match_to_history(match_dict: Dict[str, Any]) -> bool:
    """Adiciona uma partida analisada ao histórico."""
    data = load_data()
    data["matches"].insert(0, match_dict)
    data["matches"] = data["matches"][:50]
    return save_data(data)

def add_ticket_to_history(ticket_dict: Dict[str, Any]) -> bool:
    """Adiciona um bilhete gerado ao histórico (salva no Supabase e no JSON)."""
    if is_supabase_configured():
        sp_add_ticket(ticket_dict)
        
    data = load_data()
    data["tickets"].insert(0, ticket_dict)
    data["tickets"] = data["tickets"][:50]
    return save_data(data)

def get_tickets() -> list:
    """Retorna todos os bilhetes salvos no Supabase ou no JSON local."""
    if is_supabase_configured():
        sp_t = sp_get_tickets()
        if sp_t is not None:
            return sp_t
    data = load_data()
    return data.get("tickets", [])

def delete_ticket_from_history(ticket_id: str) -> bool:
    """Exclui um bilhete do histórico (do Supabase e do JSON local)."""
    if is_supabase_configured():
        sp_delete_ticket(ticket_id)
    data = load_data()
    if "tickets" in data:
        data["tickets"] = [t for t in data["tickets"] if str(t.get("id")) != str(ticket_id)]
        return save_data(data)
    return True

def clear_tickets_history() -> bool:
    """Limpa todos os bilhetes do histórico (no Supabase e no JSON local)."""
    if is_supabase_configured():
        sp_clear_tickets()
    data = load_data()
    data["tickets"] = []
    return save_data(data)

def update_leverage_progress(step: int, bankroll: float) -> bool:
    """Atualiza o progresso da alavancagem."""
    data = load_data()
    data["leverage_progress"]["current_step"] = step
    data["leverage_progress"]["current_bankroll"] = bankroll
    data["leverage_progress"]["history"].append({
        "step": step,
        "bankroll": bankroll
    })
    return save_data(data)

def add_live_signal_to_history(signal_dict: Dict[str, Any]) -> bool:
    """Salva um sinal do monitor ao vivo."""
    data = load_data()
    data["live_signals"].insert(0, signal_dict)
    data["live_signals"] = data["live_signals"][:50]
    return save_data(data)

# ====================================================
# GESTÃO DE BILHETES SIMULADOS (PAPER TRADING / SUPABASE)
# ====================================================

def get_simulated_tickets() -> list:
    """Retorna todos os bilhetes de simulação (paper trading) salvos no Supabase ou no JSON local."""
    if is_supabase_configured():
        sp_tickets = sp_get_simulated_tickets()
        if sp_tickets is not None:
            return sp_tickets

    data = load_data()
    return data.get("simulated_tickets", [])

def add_simulated_ticket(ticket_dict: Dict[str, Any]) -> bool:
    """Salva um novo bilhete simulado (no Supabase e no JSON local)."""
    saved_sp = False
    if is_supabase_configured():
        saved_sp = sp_add_simulated_ticket(ticket_dict)

    data = load_data()
    if "simulated_tickets" not in data:
        data["simulated_tickets"] = []
    data["simulated_tickets"].insert(0, ticket_dict)
    saved_json = save_data(data)

    return saved_sp or saved_json

def update_simulated_ticket(ticket_id: str, updated_fields: Dict[str, Any]) -> bool:
    """Atualiza o status e resultado de um bilhete simulado existente (no Supabase e no JSON local)."""
    if is_supabase_configured():
        sp_update_simulated_ticket(ticket_id, updated_fields)

    data = load_data()
    if "simulated_tickets" in data:
        for t in data["simulated_tickets"]:
            if str(t.get("id")) == str(ticket_id):
                t.update(updated_fields)
                return save_data(data)
    return True

def delete_simulated_ticket(ticket_id: str) -> bool:
    """Remove um bilhete simulado (do Supabase e do JSON local)."""
    if is_supabase_configured():
        sp_delete_simulated_ticket(ticket_id)

    data = load_data()
    if "simulated_tickets" in data:
        data["simulated_tickets"] = [t for t in data["simulated_tickets"] if str(t.get("id")) != str(ticket_id)]
        return save_data(data)
    return True

def clear_simulated_tickets() -> bool:
    """Limpa todo o histórico de bilhetes simulados (no Supabase e no JSON local)."""
    if is_supabase_configured():
        sp_clear_simulated_tickets()

    data = load_data()
    data["simulated_tickets"] = []
    return save_data(data)

