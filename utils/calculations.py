import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any

def calculate_implied_probability(odd: float) -> float:
    """Calcula a probabilidade implícita do mercado em % com base na Odd."""
    if odd <= 1.0:
        return 100.0
    return round((1.0 / odd) * 100.0, 2)

def calculate_ev(win_probability_perc: float, odd: float) -> float:
    """
    Calcula o Valor Esperado (+EV) de uma aposta em %.
    Fórmula: EV = (Probabilidade_Estimada * Odd) - 1
    """
    prob_decimal = win_probability_perc / 100.0
    ev = (prob_decimal * odd) - 1.0
    return round(ev * 100.0, 2)

def check_match_balance(odd_casa: float, odd_visi: float) -> Tuple[bool, float]:
    """
    Verifica se a partida é equilibrada segundo o método Múltiplas Seguras (diferença de odd <= 1.20).
    Retorna (is_parelho, diferenca_odd).
    """
    diff = abs(odd_casa - odd_visi)
    return (diff <= 1.20, round(diff, 2))

def calculate_total_odd(odds: List[float]) -> float:
    """Calcula a Odd total multiplicativa acumulada de um bilhete."""
    if not odds:
        return 1.0
    return float(round(np.prod(odds), 2))

def calculate_stake(banca_total: float, ticket_type: str) -> Dict[str, Any]:
    """
    Calcula o valor recomendado da stake com base na banca total e tipo de bilhete.
    - Múltipla Segura (Handicaps): 5.0%
    - Estatísticas Secundárias (Escanteios): 1.5%
    """
    if ticket_type == "Múltipla Segura (Handicaps)":
        percent = 5.0
        risk_level = "Baixo (Método Rígido)"
    else:
        percent = 1.5
        risk_level = "Médio (Alta Volatilidade)"

    stake_valor = (banca_total * percent) / 100.0
    return {
        "percent": percent,
        "stake_value": round(stake_valor, 2),
        "risk_level": risk_level
    }

def calculate_apm(attacks: int, minute: int) -> float:
    """Calcula os Ataques Perigosos por Minuto (APM) combinados."""
    if minute <= 0:
        return 0.0
    return round(attacks / float(minute), 2)

def generate_leverage_dataframe(banca_inicial: float, odd_media: float, etapas: int, aporte_mensal: float = 0.0, etapas_por_mes: int = 10) -> pd.DataFrame:
    """
    Gera um DataFrame com a curva matemática de crescimento da banca etapa por etapa,
    incluindo simulação de aportes mensais recorrentes.
    """
    data = []
    banca_atual = banca_inicial
    banca_sem_aporte = banca_inicial

    for i in range(etapas + 1):
        # Aporte mensal acontece a cada X etapas (ex: 10 etapas = 1 mês)
        if i > 0 and i % etapas_por_mes == 0 and aporte_mensal > 0:
            banca_atual += aporte_mensal

        lucro_etapa = banca_atual * (odd_media - 1.0) if i > 0 else 0.0
        
        data.append({
            "Etapa": i,
            "Valor Com Aportes (R$)": round(banca_atual, 2),
            "Valor Sem Aportes (R$)": round(banca_sem_aporte, 2),
            "Lucro na Etapa (R$)": round(lucro_etapa, 2)
        })

        if i < etapas:
            banca_atual = banca_atual * odd_media
            banca_sem_aporte = banca_sem_aporte * odd_media

    return pd.DataFrame(data)

def calculate_xg_and_defense(odd_casa: float, odd_empate: float, odd_visi: float) -> Dict[str, Any]:
    """
    Calcula o xG (Expectativa de Gols) e Poder Defensivo (Índice de Solidez e Clean Sheets)
    com base nas probabilidades implícitas de mercado e distribuição estatística de Poisson.
    """
    odd_c = max(float(odd_casa), 1.05)
    odd_e = max(float(odd_empate), 1.05) if float(odd_empate) > 1.0 else 3.10
    odd_v = max(float(odd_visi), 1.05)
    
    # Probabilidades brutas
    p_c = 1.0 / odd_c
    p_e = 1.0 / odd_e
    p_v = 1.0 / odd_v
    soma_p = p_c + p_e + p_v
    
    prob_casa = p_c / soma_p
    prob_emp = p_e / soma_p
    prob_visi = p_v / soma_p
    
    # Expectativa de Gols da partida (Jogos parelhos com alta chance de empate têm menor xG total)
    total_xg = round(max(1.50, min(3.20, 2.50 - (prob_emp * 1.6))), 2)
    
    prob_gols_relativo = prob_casa + prob_visi
    xg_casa = round(total_xg * (prob_casa / prob_gols_relativo), 2)
    xg_visi = round(total_xg * (prob_visi / prob_gols_relativo), 2)
    
    # Probabilidade de Clean Sheet (não sofrer gols) via Poisson P(0) = exp(-xG_sofrido)
    clean_sheet_casa_pct = round(np.exp(-xg_visi) * 100.0, 1)
    clean_sheet_visi_pct = round(np.exp(-xg_casa) * 100.0, 1)
    
    # Poder Defensivo (Score de 0 a 100)
    poder_def_casa = int(min(max(100 - (xg_visi * 45), 30), 95))
    poder_def_visi = int(min(max(100 - (xg_casa * 45), 30), 95))
    
    # Classificação de Segurança para o método Múltiplas Seguras
    if total_xg <= 2.05:
        seguranca_label = "🟢 Alta Segurança (Baixo xG / Jogo Amarrado)"
        seguranca_status = "Excelente"
    elif total_xg <= 2.40:
        seguranca_label = "🟡 Segurança Moderada (Equilibrado)"
        seguranca_status = "Moderado"
    else:
        seguranca_label = "🔴 Risco Elevado (Tendência Over)"
        seguranca_status = "Risco"
        
    return {
        "xg_total": total_xg,
        "xg_casa": xg_casa,
        "xg_visi": xg_visi,
        "clean_sheet_casa": clean_sheet_casa_pct,
        "clean_sheet_visi": clean_sheet_visi_pct,
        "poder_def_casa": poder_def_casa,
        "poder_def_visi": poder_def_visi,
        "seguranca_label": seguranca_label,
        "seguranca_status": seguranca_status
    }

def calculate_team_corners(escanteios_total: Any, odd_casa: float, odd_visi: float) -> Dict[str, float]:
    """
    Calcula a distribuição esperada de escanteios (ExC) para o time da Casa e Visitante
    com base no total de escanteios projetados e no volume ofensivo implícito das odds.
    """
    try:
        total = float(escanteios_total)
        if total <= 0:
            total = 9.5
    except (ValueError, TypeError):
        total = 9.5
        
    odd_c = max(float(odd_casa), 1.05)
    odd_v = max(float(odd_visi), 1.05)
    
    # Probabilidade implícita de domínio ofensivo
    p_c = 1.0 / odd_c
    p_v = 1.0 / odd_v
    soma = p_c + p_v
    
    # Peso de controle de jogo (mandante x visitante)
    share_casa = (p_c / soma) * 0.40 + 0.30
    share_casa = max(0.35, min(0.70, share_casa))
    share_visi = 1.0 - share_casa
    
    exc_casa = round(total * share_casa, 1)
    exc_visi = round(total * share_visi, 1)
    
    return {
        "exc_total": round(total, 1),
        "exc_casa": exc_casa,
        "exc_visi": exc_visi,
        "share_casa_pct": round(share_casa * 100, 1),
        "share_visi_pct": round(share_visi * 100, 1)
    }

def is_brazil_serie_b(pais: str = "", liga: str = "", label: str = "", time_casa: str = "", time_visi: str = "") -> bool:
    """
    Verifica com precisão se a partida pertence à Série B do Campeonato Brasileiro.
    Filtra variações como 'Série B', 'Serie B', 'Brasileirão Série B', etc., restrito ao Brasil.
    Ligas de outros países (como Serie B da Itália) são preservadas.
    """
    pais_lower = str(pais or "").strip().lower()
    liga_lower = str(liga or "").strip().lower()
    label_lower = str(label or "").strip().lower()
    
    # Termos indicativos de Série B / Segunda Divisão
    serie_b_keywords = [
        "serie b", "série b", "serie-b", "série-b", 
        "brasileirao b", "brasileirão b", "brasileiro b", 
        "segunda divisão", "segunda divisao", "2ª divisão", "2a divisao"
    ]
    
    # Nomes explícitos de liga brasileira Série B
    explicit_br_b = [
        "brasileirão série b", "brasileirao serie b", "brasileiro serie b", 
        "brasileiro série b", "brazil serie b", "brazil série b", 
        "campeonato brasileiro série b", "campeonato brasileiro serie b",
        "campeonato brasileiro b", "campeonato brasileiro - serie b", "campeonato brasileiro - série b"
    ]
    if any(k in liga_lower for k in explicit_br_b) or any(k in label_lower for k in explicit_br_b):
        return True

    # Se o país é Brasil (BRA, BR, Brasil, Brazil)
    is_brazil = (
        pais_lower in ["bra", "brasil", "brazil", "br"] or 
        "brasileir" in liga_lower or 
        "[br" in label_lower or 
        "brasileirao" in label_lower or 
        "brasileirão" in label_lower
    )
    
    if is_brazil and any(kw in liga_lower for kw in serie_b_keywords):
        return True
        
    if is_brazil and any(kw in label_lower for kw in serie_b_keywords):
        return True
        
    return False

def filter_out_serie_b(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove todas as partidas da Série B do Campeonato Brasileiro de uma lista de partidas."""
    filtered = []
    for m in matches:
        if not is_brazil_serie_b(
            pais=m.get("pais", ""),
            liga=m.get("liga", ""),
            label=m.get("label", ""),
            time_casa=m.get("time_casa", ""),
            time_visi=m.get("time_visi", "")
        ):
            filtered.append(m)
    return filtered

def get_country_flag(pais: str) -> str:
    """Retorna o emoji da bandeira correspondente ao código ou nome do país."""
    p = str(pais or "").strip().upper()
    flags = {
        "ESP": "🇪🇸", "ESPANHA": "🇪🇸", "SPAIN": "🇪🇸",
        "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "INGLATERRA": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "ENGLAND": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "GBR": "🇬🇧",
        "BRA": "🇧🇷", "BRASIL": "🇧🇷", "BRAZIL": "🇧🇷",
        "ARG": "🇦🇷", "ARGENTINA": "🇦🇷",
        "ITA": "🇮🇹", "ITÁLIA": "🇮🇹", "ITALY": "🇮🇹",
        "GER": "🇩🇪", "ALEMANHA": "🇩🇪", "GERMANY": "🇩🇪", "DEU": "🇩🇪",
        "FRA": "🇫🇷", "FRANÇA": "🇫🇷", "FRANCE": "🇫🇷",
        "POR": "🇵🇹", "PORTUGAL": "🇵🇹",
        "FIN": "🇫🇮", "FINLÂNDIA": "🇫🇮", "FINLAND": "🇫🇮",
        "USA": "🇺🇸", "ESTADOS UNIDOS": "🇺🇸",
        "MEX": "🇲🇽", "MÉXICO": "🇲🇽", "MEXICO": "🇲🇽",
        "COL": "🇨🇴", "COLÔMBIA": "🇨🇴", "COLOMBIA": "🇨🇴",
        "NED": "🇳🇱", "HOLANDA": "🇳🇱", "NETHERLANDS": "🇳🇱",
        "TUR": "🇹🇷", "TURQUIA": "🇹🇷", "TURKEY": "🇹🇷",
        "URU": "🇺🇾", "URUGUAI": "🇺🇾", "URUGUAY": "🇺🇾",
        "PAR": "🇵🇾", "PARAGUAI": "🇵🇾", "PARAGUAY": "🇵🇾",
        "CHI": "🇨🇱", "CHILE": "🇨🇱",
        "BEL": "🇧🇪", "BÉLGICA": "🇧🇪", "BELGIUM": "🇧🇪",
        "NOR": "🇳🇴", "NORUEGA": "🇳🇴", "NORWAY": "🇳🇴",
        "SWE": "🇸🇪", "SUÉCIA": "🇸🇪", "SWEDEN": "🇸🇪",
        "DEN": "🇩🇰", "DINAMARCA": "🇩🇰", "DENMARK": "🇩🇰",
        "AUT": "🇦🇹", "ÁUSTRIA": "🇦🇹", "AUSTRIA": "🇦🇹",
        "SUI": "🇨🇭", "SUÍÇA": "🇨🇭", "SWITZERLAND": "🇨🇭", "CHE": "🇨🇭",
        "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "ESCÓCIA": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "SCOTLAND": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "GRE": "🇬🇷", "GRÉCIA": "🇬🇷", "GREECE": "🇬🇷",
        "KOR": "🇰🇷", "CORÉIA": "🇰🇷", "KOREA": "🇰🇷",
        "JPN": "🇯🇵", "JAPÃO": "🇯🇵", "JAPAN": "🇯🇵",
        "SAU": "🇸🇦", "ARÁBIA": "🇸🇦", "SAUDI": "🇸🇦",
    }
    return flags.get(p, "🏆")

def get_country_display_name(pais: str) -> str:
    """Retorna o nome do país formatado em português."""
    p = str(pais or "").strip().upper()
    names = {
        "BRA": "Brasil", "BRASIL": "Brasil", "BRAZIL": "Brasil",
        "ESP": "Espanha", "ESPANHA": "Espanha", "SPAIN": "Espanha",
        "ENG": "Inglaterra", "INGLATERRA": "Inglaterra", "ENGLAND": "Inglaterra", "GBR": "Reino Unido",
        "ARG": "Argentina", "ARGENTINA": "Argentina",
        "ITA": "Itália", "ITÁLIA": "Itália", "ITALY": "Itália",
        "GER": "Alemanha", "ALEMANHA": "Alemanha", "GERMANY": "Alemanha", "DEU": "Alemanha",
        "FRA": "França", "FRANÇA": "França", "FRANCE": "França",
        "POR": "Portugal", "PORTUGAL": "Portugal",
        "FIN": "Finlândia", "FINLÂNDIA": "Finlândia", "FINLAND": "Finlândia",
        "USA": "EUA", "ESTADOS UNIDOS": "EUA",
        "MEX": "México", "MÉXICO": "México",
        "COL": "Colômbia", "COLÔMBIA": "Colômbia",
        "NED": "Holanda", "HOLANDA": "Holanda",
        "TUR": "Turquia", "TURQUIA": "Turquia",
        "URU": "Uruguai", "URUGUAI": "Uruguai",
        "PAR": "Paraguai", "PARAGUAI": "Paraguai",
        "CHI": "Chile", "CHILE": "Chile",
        "BEL": "Bélgica", "BÉLGICA": "Bélgica",
        "NOR": "Noruega", "NORUEGA": "Noruega",
        "SWE": "Suécia", "SUÉCIA": "Suécia",
        "DEN": "Dinamarca", "DINAMARCA": "Dinamarca",
        "AUT": "Áustria", "ÁUSTRIA": "Áustria",
        "SUI": "Suíça", "SUÍÇA": "Suíça",
        "SCO": "Escócia", "ESCÓCIA": "Escócia",
        "GRE": "Grécia", "GRÉCIA": "Grécia",
    }
    return names.get(p, str(pais or "").strip())

def group_matches_by_league(matches: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Agrupa as partidas por Liga/Campeonato, garantindo que os jogos da mesma liga
    fiquem organizados juntos em suas respectivas abas/seções.
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for m in matches:
        liga = m.get("liga", "").strip() or "Outras Ligas"
        pais = m.get("pais", "").strip()
        
        flag = get_country_flag(pais)
        country_name = get_country_display_name(pais)
        
        if country_name and country_name.lower() not in liga.lower():
            league_key = f"{flag} {liga} ({country_name})"
        else:
            league_key = f"{flag} {liga}"
            
        if league_key not in grouped:
            grouped[league_key] = []
        grouped[league_key].append(m)
        
    # Ordena pelo número de jogos de forma decrescente
    sorted_grouped = dict(sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])))
    return sorted_grouped


