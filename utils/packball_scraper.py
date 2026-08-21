import asyncio
from playwright.async_api import async_playwright
import time
import json

async def scrape_packball(email, password, num_days=7):
    matches = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            # 1. Login
            print(f"Tentando logar com {email}")
            await page.goto("https://packball.com/pt/login", wait_until="domcontentloaded", timeout=60000)
            
            try:
                await page.wait_for_selector('input[name="email"], input[type="email"]', timeout=10000)
                await page.fill('input[name="email"], input[type="email"]', email)
                await page.fill('input[name="password"], input[type="password"]', password)
                await page.click('.btn-login button, button:has-text("Entrar")')
                try:
                    await page.wait_for_url("**/matches**", timeout=15000)
                except Exception:
                    await page.wait_for_timeout(5000)
            except Exception as e:
                print("Login já efetuado ou formulário não encontrado:", e)
                
            # 2. Navegar para Matches (garantindo estar logado)
            print("Navegando para Matches...")
            if not page.url.endswith("/matches"):
                await page.goto("https://packball.com/pt/matches")
            await page.wait_for_timeout(4000)
            await page.screenshot(path="debug_state.png")
            
            seen_match_keys = set()
            
            # 3. Loop pelos dias configurados pelo usuário
            total_dias = max(1, min(int(num_days), 14))
            for day in range(total_dias):
                current_date = await page.evaluate(r'''() => {
                    const el = document.querySelector('.arrow-nav .title-active');
                    return el ? el.innerText.trim() : null;
                }''')
                if not current_date:
                    current_date = f"Dia {day+1}"
                print(f"Buscando {current_date} (Passo {day+1}/{total_dias})...")
                
                # Extrair jogos do dia atual com métricas VIP completas
                day_matches = await page.evaluate(r'''() => {
                    const matchRows = Array.from(document.querySelectorAll('ul.row'));
                    const results = [];
                    
                    for (const row of matchRows) {
                        const html = row.innerHTML;
                        
                        // Times
                        const teamHomes = Array.from(row.querySelectorAll('.team-name-home .team-home'));
                        const teamAways = Array.from(row.querySelectorAll('.team-name-away .team-away'));
                        if (teamHomes.length === 0 || teamAways.length === 0) continue;
                        
                        const time_casa = teamHomes[0].textContent.trim();
                        const time_visi = teamAways[0].textContent.trim();
                        
                        // Liga, País e Horário
                        const countryEl = row.querySelector('.short-country');
                        const leagueEl = row.querySelector('.title-league span');
                        const timeEl = row.querySelector('.time time');
                        
                        const pais = countryEl ? countryEl.textContent.trim() : '';
                        const liga = leagueEl ? leagueEl.textContent.trim() : '';
                        const horario = timeEl ? timeEl.textContent.trim() : '';
                        
                        // Odds
                        const oddCells = Array.from(row.querySelectorAll('li.col.custom.odds'));
                        let odd_casa = 2.0;
                        let odd_visi = 2.0;
                        if (oddCells.length > 0) {
                            const val = parseFloat(oddCells[0].textContent.trim());
                            if (!isNaN(val)) odd_casa = val;
                        }
                        if (oddCells.length > 1) {
                            const val = parseFloat(oddCells[1].textContent.trim());
                            if (!isNaN(val)) odd_visi = val;
                        }
                        
                        // Verificar estrela vazada (Sem favorito ou leve favoritismo)
                        const is_hollow_star = html.includes('Sem favorito') || 
                                               html.includes('leve favoritismo') || 
                                               row.querySelector('li.col.custom.b3.tt i.default') !== null;
                        
                        // Colunas VIP do Packball
                        const customCols = Array.from(row.querySelectorAll('li.col.custom'));
                        let win_prob = '';
                        let ppg = '';
                        let gols_avg = '';
                        let exg = 2.2;
                        let over25 = '';
                        let bts = '';
                        let escanteios_avg = '';
                        let escanteios_exc = '';
                        
                        if (customCols.length >= 4) win_prob = customCols[3].innerText.replace(/\n/g, ' ').trim();
                        if (customCols.length >= 6) ppg = customCols[5].innerText.replace(/\n/g, ' ').trim();
                        if (customCols.length >= 7) gols_avg = customCols[6].innerText.trim();
                        if (customCols.length >= 8) {
                            const parsedExg = parseFloat(customCols[7].innerText.trim());
                            if (!isNaN(parsedExg)) {
                                exg = parsedExg;
                            } else {
                                const parsedAvg = parseFloat(gols_avg);
                                if (!isNaN(parsedAvg)) exg = parsedAvg;
                            }
                        }
                        if (customCols.length >= 9) over25 = customCols[8].innerText.trim();
                        if (customCols.length >= 10) bts = customCols[9].innerText.trim();
                        if (customCols.length >= 11) escanteios_avg = customCols[10].innerText.trim();
                        if (customCols.length >= 12) escanteios_exc = customCols[11].innerText.trim();
                        
                        if (is_hollow_star) {
                            results.push({
                                time_casa: time_casa,
                                time_visi: time_visi,
                                pais: pais,
                                liga: liga,
                                horario: horario,
                                odd_casa: odd_casa,
                                odd_visi: odd_visi,
                                win_prob: win_prob,
                                ppg: ppg,
                                gols_avg: gols_avg,
                                exg: exg,
                                over25: over25,
                                bts: bts,
                                escanteios_avg: escanteios_avg,
                                escanteios_exc: escanteios_exc
                            });
                        }
                    }
                    return results;
                }''')
                
                for m in day_matches:
                    match_key = f"{current_date}_{m['time_casa']}_{m['time_visi']}"
                    if match_key not in seen_match_keys:
                        seen_match_keys.add(match_key)
                        matches.append({
                            "id": f"pack_{day}_{m['time_casa']}",
                            "time_casa": m['time_casa'],
                            "time_visi": m['time_visi'],
                            "pais": m['pais'],
                            "liga": m['liga'],
                            "horario": m['horario'],
                            "odd_casa": m['odd_casa'],
                            "odd_empate": 3.10,
                            "odd_visi": m['odd_visi'],
                            "win_prob": m['win_prob'],
                            "ppg": m['ppg'],
                            "gols_avg": m['gols_avg'],
                            "exg": m['exg'],
                            "over25": m['over25'],
                            "bts": m['bts'],
                            "escanteios_avg": m['escanteios_avg'],
                            "escanteios_exc": m['escanteios_exc'],
                            "data": current_date,
                            "mercado": "Handicap",
                        })
                
                # Clicar na seta para o próximo dia no canto superior esquerdo (.arrow-next)
                try:
                    await page.locator('.arrow-nav .arrow-next, .arrow-next').click()
                    await page.wait_for_timeout(3500)
                except Exception as e:
                    print("Fim dos dias ou erro ao avançar para o próximo dia:", e)
                    break
                    
        except Exception as e:
            print("Erro no scraping:", e)
            return {"error": str(e)}
        finally:
            await browser.close()
            
    return matches

import concurrent.futures
import os

def fetch_packball_matches(username, password, num_days=7):
    """
    Função wrapper síncrona que roda o scraper assíncrono em uma thread isolada.
    Recebe o número de dias desejado para a extração (1 a 14 dias).
    """
    def _run():
        return asyncio.run(scrape_packball(username, password, num_days=num_days))
        
    res = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            res = future.result(timeout=180)
    except Exception as e:
        print(f"Aviso no Playwright: {e}")
        
    if isinstance(res, list) and len(res) > 0:
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/cached_packball.json", "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return res
        
    # Fallback para o cache recente
    try:
        if os.path.exists("data/cached_packball.json"):
            with open("data/cached_packball.json", "r", encoding="utf-8") as f:
                cached = json.load(f)
                if cached and len(cached) > 0:
                    return cached
    except Exception:
        pass
        
    return res if res else {"error": "Limite diário de requisições do Packball atingido. Tente novamente mais tarde."}
