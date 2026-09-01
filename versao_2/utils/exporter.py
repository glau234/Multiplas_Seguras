from typing import Dict, Any

def format_match_analysis(data: Dict[str, Any]) -> str:
    """Gera texto formatado de análise de partida para envio no Telegram/WhatsApp."""
    return f"""⚽ *ANÁLISE DE PARTIDA - MÚLTIPLAS SEGURAS*
🏆 *Confronto:* {data.get('time_casa')} x {data.get('time_visi')}
📊 *Odds:* Casa {data.get('odd_casa')} | Empate {data.get('odd_empate')} | Visitante {data.get('odd_visi')}
⚽ *xG Projetado:* {data.get('xg_partida')} gols
📈 *Diagnóstico:* {data.get('diagnostico')}
🎯 *Recomendação:* {data.get('recomendacao')}
💡 *EV+ Estimado:* {data.get('ev_percent', 0)}%
---
_Método Múltiplas Seguras - Gestão & Qualidade_"""

def format_ticket_summary(ticket_data: Dict[str, Any]) -> str:
    """Gera texto formatado de bilhete pronto para cópia rápida."""
    linhas_jogos = []
    for idx, sel in enumerate(ticket_data.get('selecoes', []), 1):
        linhas_jogos.append(f"  {idx}. {sel.get('jogo')} ({sel.get('horario')}) ➔ *{sel.get('selecao')}* @{sel.get('odd')}")
    
    jogos_str = "\n".join(linhas_jogos)

    return f"""📝 *BILHETE GERADO - {ticket_data.get('tipo_bilhete').upper()}*
📌 *Seleções:*
{jogos_str}

🔥 *Odd Total:* {ticket_data.get('odd_total'):.2f}
💰 *Stake Recomendada:* R$ {ticket_data.get('stake_valor'):.2f} ({ticket_data.get('stake_percent')}%)
💵 *Retorno Potencial:* R$ {ticket_data.get('retorno_potencial'):.2f}
💵 *Lucro Líquido:* R$ {ticket_data.get('lucro_liquido'):.2f}
---
_Gerado via Múltiplas Seguras App_"""

def format_live_signal(signal_data: Dict[str, Any]) -> str:
    """Gera texto formatado de sinal ao vivo da estratégia Mina de Ouro."""
    return f"""🔥 *ALERTA AO VIVO - ESTRATÉGIA MINA DE OURO*
⚽ *Jogo:* {signal_data.get('jogo')} ({signal_data.get('minuto')} min)
📊 *Placar Atual:* {signal_data.get('placar_casa')} x {signal_data.get('placar_visi')}
⚡ *APM Combinado:* {signal_data.get('apm'):.2f} ataques/min
🎯 *Finalizações:* {signal_data.get('finalizacoes')} no gol

🟢 *OPERAÇÃO DUPLO GREEN SUGERIDA:*
1️⃣ *Over Gols Limite 2H*
2️⃣ *Ambas Marcam no 2º Tempo (BTTS 2H)*

⚠️ *Checklist Cash Out:* Encerrar se o ritmo desacelerar após 1 gol!
---
_Monitor Mina de Ouro Ao Vivo_"""
