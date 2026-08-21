import json
import os
from typing import Dict, Any

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
            "live_signals": []
        }
        save_data(initial_data)

def load_data() -> Dict[str, Any]:
    """Carrega todos os dados armazenados no arquivo JSON."""
    ensure_data_file()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler histórico JSON: {e}")
        return {
            "matches": [],
            "tickets": [],
            "leverage_progress": {"current_step": 0, "current_bankroll": 100.0, "target_bankroll": 1378061.0, "history": []},
            "live_signals": []
        }

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
    data["matches"].insert(0, match_dict)  # Insere no topo
    data["matches"] = data["matches"][:50]  # Limita aos últimos 50
    return save_data(data)

def add_ticket_to_history(ticket_dict: Dict[str, Any]) -> bool:
    """Adiciona um bilhete gerado ao histórico."""
    data = load_data()
    data["tickets"].insert(0, ticket_dict)
    data["tickets"] = data["tickets"][:50]
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
