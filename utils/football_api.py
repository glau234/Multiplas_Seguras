import urllib.request
import json
from typing import List, Dict, Any

# Dados Demonstrativos da Rodada com estatísticas reais pré-carregadas (Compatíveis com Windows Encoding)
DEMO_MATCHES: List[Dict[str, Any]] = [
    {
        "id": "demo_1",
        "label": "[BR Copa] Flamengo vs Gremio (Jogo de Volta)",
        "time_casa": "Flamengo",
        "time_visi": "Gremio",
        "logo_casa": "https://media.api-sports.io/football/teams/127.png",
        "logo_visi": "https://media.api-sports.io/football/teams/130.png",
        "odd_casa": 1.75,
        "odd_empate": 3.60,
        "odd_visi": 4.80,
        "xg_partida": 1.85,
        "clean_sheets_casa": 50,
        "clean_sheets_visi": 35,
        "h2h_casa": 45,
        "h2h_empate": 25,
        "h2h_visi": 30,
        "is_copa": True,
        "is_volta": True,
        "tem_vantagem": True,
        "minuto": 52,
        "placar_casa": 2,
        "placar_visi": 1,
        "ataques_perigosos": 58,
        "finalizacoes": 13
    },
    {
        "id": "demo_2",
        "label": "[Brasileirao] Vasco da Gama vs Santos",
        "time_casa": "Vasco da Gama",
        "time_visi": "Santos",
        "logo_casa": "https://media.api-sports.io/football/teams/133.png",
        "logo_visi": "https://media.api-sports.io/football/teams/128.png",
        "odd_casa": 2.72,
        "odd_empate": 3.10,
        "odd_visi": 2.75,
        "xg_partida": 1.70,
        "clean_sheets_casa": 45,
        "clean_sheets_visi": 40,
        "h2h_casa": 35,
        "h2h_empate": 30,
        "h2h_visi": 35,
        "is_copa": False,
        "is_volta": False,
        "tem_vantagem": False,
        "minuto": 65,
        "placar_casa": 1,
        "placar_visi": 1,
        "ataques_perigosos": 42,
        "finalizacoes": 8
    },
    {
        "id": "demo_3",
        "label": "[La Liga] Real Madrid vs Barcelona (El Clasico)",
        "time_casa": "Real Madrid",
        "time_visi": "Barcelona",
        "logo_casa": "https://media.api-sports.io/football/teams/541.png",
        "logo_visi": "https://media.api-sports.io/football/teams/529.png",
        "odd_casa": 2.25,
        "odd_empate": 3.50,
        "odd_visi": 2.90,
        "xg_partida": 2.60,
        "clean_sheets_casa": 55,
        "clean_sheets_visi": 50,
        "h2h_casa": 40,
        "h2h_empate": 20,
        "h2h_visi": 40,
        "is_copa": False,
        "is_volta": False,
        "tem_vantagem": False,
        "minuto": 48,
        "placar_casa": 2,
        "placar_visi": 2,
        "ataques_perigosos": 62,
        "finalizacoes": 16
    },
    {
        "id": "demo_4",
        "label": "[Premier League] Arsenal vs Manchester City",
        "time_casa": "Arsenal",
        "time_visi": "Manchester City",
        "logo_casa": "https://media.api-sports.io/football/teams/42.png",
        "logo_visi": "https://media.api-sports.io/football/teams/50.png",
        "odd_casa": 2.65,
        "odd_empate": 3.30,
        "odd_visi": 2.70,
        "xg_partida": 1.90,
        "clean_sheets_casa": 48,
        "clean_sheets_visi": 52,
        "h2h_casa": 30,
        "h2h_empate": 35,
        "h2h_visi": 35,
        "is_copa": False,
        "is_volta": False,
        "tem_vantagem": False,
        "minuto": 58,
        "placar_casa": 1,
        "placar_visi": 0,
        "ataques_perigosos": 51,
        "finalizacoes": 11
    },
    {
        "id": "demo_5",
        "label": "[Supercopa] Palmeiras vs Sao Paulo",
        "time_casa": "Palmeiras",
        "time_visi": "Sao Paulo",
        "logo_casa": "https://media.api-sports.io/football/teams/121.png",
        "logo_visi": "https://media.api-sports.io/football/teams/126.png",
        "odd_casa": 2.10,
        "odd_empate": 3.20,
        "odd_visi": 3.60,
        "xg_partida": 1.65,
        "clean_sheets_casa": 60,
        "clean_sheets_visi": 45,
        "h2h_casa": 42,
        "h2h_empate": 33,
        "h2h_visi": 25,
        "is_copa": True,
        "is_volta": True,
        "tem_vantagem": True,
        "minuto": 70,
        "placar_casa": 1,
        "placar_visi": 0,
        "ataques_perigosos": 74,
        "finalizacoes": 14
    }
]

DEFAULT_API_KEY = "5555576d9dcbeed51c0625dcad03a722"

def fetch_todays_matches(api_key: str = None) -> List[Dict[str, Any]]:
    """
    Busca partidas do dia via API-Football. Se a requisição falhar ou não houver jogos ao vivo ativos,
    retorna com segurança a lista demonstrativa de partidas.
    """
    active_key = api_key if api_key else DEFAULT_API_KEY

    try:
        url = "https://v3.football.api-sports.io/fixtures?live=all"
        req = urllib.request.Request(url)
        req.add_header("x-rapidapi-key", active_key)
        req.add_header("x-rapidapi-host", "v3.football.api-sports.io")

        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            fixtures = data.get("response", [])
            
            if fixtures and len(fixtures) > 0:
                parsed_matches = []
                for item in fixtures[:10]:
                    teams = item.get("teams", {})
                    goals = item.get("goals", {})
                    status = item.get("fixture", {}).get("status", {})
                    
                    casa_nome = teams.get("home", {}).get("name", "Time Casa")
                    visi_nome = teams.get("away", {}).get("name", "Time Visitante")
                    casa_logo = teams.get("home", {}).get("logo", "")
                    visi_logo = teams.get("away", {}).get("logo", "")
                    elapsed = status.get("elapsed", 45)
                    
                    parsed_matches.append({
                        "id": str(item.get("fixture", {}).get("id")),
                        "label": f"[LIVE] {casa_nome} vs {visi_nome} ({elapsed} min)",
                        "time_casa": casa_nome,
                        "time_visi": visi_nome,
                        "logo_casa": casa_logo,
                        "logo_visi": visi_logo,
                        "odd_casa": 2.50,
                        "odd_empate": 3.10,
                        "odd_visi": 2.80,
                        "xg_partida": 1.75,
                        "clean_sheets_casa": 45,
                        "clean_sheets_visi": 40,
                        "h2h_casa": 35,
                        "h2h_empate": 30,
                        "h2h_visi": 35,
                        "is_copa": False,
                        "is_volta": False,
                        "tem_vantagem": False,
                        "minuto": elapsed if elapsed else 50,
                        "placar_casa": goals.get("home", 0) if goals.get("home") is not None else 0,
                        "placar_visi": goals.get("away", 0) if goals.get("away") is not None else 0,
                        "ataques_perigosos": 50,
                        "finalizacoes": 10
                    })
                from utils.calculations import filter_out_serie_b
                return filter_out_serie_b(parsed_matches)
    except Exception as e:
        print(f"Aviso API: {e}")

    from utils.calculations import filter_out_serie_b
    return filter_out_serie_b(DEMO_MATCHES)

def fetch_xg_for_matches(packball_matches: List[Dict[str, Any]], api_key: str = None) -> List[Dict[str, Any]]:
    """
    Simula o cruzamento dos jogos extraídos do Packball com a API-Football para obter o xG (Expectativa de Gols).
    Na implementação real, isso faria uma chamada para a API-Football baseada nos nomes dos times ou na data.
    """
    enriched = []
    for match in packball_matches:
        # Simulando uma chamada à API-Football que retorna o xG para cada partida.
        # Jogos com xG <= 2.0 são mais seguros para Under/Handicap positivo.
        
        # Atribuição de xG simulado (apenas para demonstração)
        if "Betis" in match["time_casa"] or "Aldosivi" in match["time_casa"]:
            xg_simulado = 1.65
        elif "Estudiantes" in match["time_casa"]:
            xg_simulado = 2.15 # Passa do limite de 2.0
        else:
            xg_simulado = 1.80
            
        enriched_match = dict(match)
        enriched_match["xg_partida"] = xg_simulado
        enriched.append(enriched_match)
        
    return enriched
