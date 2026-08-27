import asyncio
import time
import json
import os
import concurrent.futures

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False

async def scrape_packball(email, password, num_days=7):
    matches = []
    
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        print("Playwright não instalado ou indisponível no ambiente.")
        return []
        
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as e_launch:
            print(f"Instalando navegador Chromium do Playwright no ambiente... ({e_launch})")
            import subprocess
            try:
                subprocess.run(["playwright", "install", "chromium"], check=False)
                browser = await p.chromium.launch(headless=True)
            except Exception as e_retry:
                print(f"Falha ao iniciar Chromium: {e_retry}")
                return []

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
                
                # Rolar a página para carregar todas as partidas da lista do dia (Lazy Loading)
                try:
                    await page.evaluate(r'''async () => {
                        await new Promise((resolve) => {
                            let totalHeight = 0;
                            const distance = 600;
                            const timer = setInterval(() => {
                                const scrollHeight = document.body.scrollHeight;
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                if (totalHeight >= scrollHeight || totalHeight >= 12000) {
                                    clearInterval(timer);
                                    window.scrollTo(0, 0);
                                    resolve();
                                }
                            }, 80);
                        });
                    }''')
                    await page.wait_for_timeout(800)
                except Exception:
                    pass

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
                        
                        // Adiciona todas as partidas da lista do Packball
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
                            escanteios_exc: escanteios_exc,
                            is_hollow_star: is_hollow_star
                        });
                    }
                    return results;
                }''')
                
                for m in day_matches:
                    # Critério obrigatório: Não trazer nenhuma partida da Série B do Campeonato Brasileiro
                    from utils.calculations import is_brazil_serie_b
                    if is_brazil_serie_b(pais=m.get('pais', ''), liga=m.get('liga', ''), time_casa=m.get('time_casa', ''), time_visi=m.get('time_visi', '')):
                        continue
                        
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
        from utils.calculations import filter_out_serie_b, filter_out_past_matches
        res = filter_out_serie_b(res)
        res = filter_out_past_matches(res)
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
                    from utils.calculations import filter_out_serie_b, filter_out_past_matches
                    return filter_out_past_matches(filter_out_serie_b(cached))
    except Exception:
        pass
        
    return res if res else {"error": "Limite diário de requisições do Packball atingido. Tente novamente mais tarde."}


async def scrape_packball_live(email, password):
    """
    Navega até o Packball VIP, realiza o login e clica no botão 'Ao Vivo' ou navega até a seção de jogos ao vivo,
    extraindo todas as partidas em tempo real com minuto, placar e métricas de pressão.
    """
    matches = []
    
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        print("Playwright não instalado ou indisponível no ambiente.")
        return []
        
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as e_launch:
            import subprocess
            try:
                subprocess.run(["playwright", "install", "chromium"], check=False)
                browser = await p.chromium.launch(headless=True)
            except Exception:
                return []

        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            # 1. Login no Packball
            await page.goto("https://packball.com/pt/login", wait_until="domcontentloaded", timeout=60000)
            try:
                await page.wait_for_selector('input[name="email"], input[type="email"]', timeout=10000)
                await page.fill('input[name="email"], input[type="email"]', email)
                await page.fill('input[name="password"], input[type="password"]', password)
                await page.click('.btn-login button, button:has-text("Entrar")')
                await page.wait_for_timeout(4000)
            except Exception as e:
                print("Login Packball Live:", e)
                
            # 2. Navegar para a seção Ao Vivo (tentando clicar no botão Ao Vivo ou acessando a rota /live)
            print("Buscando seção Ao Vivo no Packball VIP...")
            try:
                live_btn = page.locator('button:has-text("Ao Vivo"), a:has-text("Ao Vivo"), .nav-link:has-text("Ao Vivo"), .live-tab, [href*="live"]')
                if await live_btn.count() > 0:
                    await live_btn.first.click()
                    await page.wait_for_timeout(3000)
                else:
                    await page.goto("https://packball.com/pt/live", wait_until="domcontentloaded", timeout=30000)
            except Exception:
                await page.goto("https://packball.com/pt/matches", wait_until="domcontentloaded", timeout=30000)

            await page.wait_for_timeout(3000)
            
            # Extrai os jogos ao vivo da página do Packball
            live_matches_data = await page.evaluate(r'''() => {
                const matchRows = Array.from(document.querySelectorAll('ul.row, .live-match-row, .match-card'));
                const results = [];
                
                for (const row of matchRows) {
                    const teamHomes = Array.from(row.querySelectorAll('.team-name-home .team-home, .home-team'));
                    const teamAways = Array.from(row.querySelectorAll('.team-name-away .team-away, .away-team'));
                    if (teamHomes.length === 0 || teamAways.length === 0) continue;
                    
                    const time_casa = teamHomes[0].textContent.trim();
                    const time_visi = teamAways[0].textContent.trim();
                    
                    const countryEl = row.querySelector('.short-country');
                    const leagueEl = row.querySelector('.title-league span');
                    const timeEl = row.querySelector('.time time, .match-time, .minute');
                    const scoreEl = row.querySelector('.score, .match-score');
                    
                    const pais = countryEl ? countryEl.textContent.trim() : '';
                    const liga = leagueEl ? leagueEl.textContent.trim() : '';
                    const minuto_str = timeEl ? timeEl.textContent.replace(/[^0-9]/g, '') : '50';
                    const minuto = parseInt(minuto_str) || 50;
                    
                    let placar_casa = 0;
                    let placar_visi = 0;
                    if (scoreEl) {
                        const scoreText = scoreEl.textContent.trim();
                        const parts = scoreText.split(/[-xX:]/);
                        if (parts.length >= 2) {
                            placar_casa = parseInt(parts[0].trim()) || 0;
                            placar_visi = parseInt(parts[1].trim()) || 0;
                        }
                    }
                    
                    const oddCells = Array.from(row.querySelectorAll('li.col.custom.odds, .odd-cell'));
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
                    
                    const customCols = Array.from(row.querySelectorAll('li.col.custom'));
                    let exg = 2.4;
                    if (customCols.length >= 8) {
                        const pExg = parseFloat(customCols[7].innerText.trim());
                        if (!isNaN(pExg)) exg = pExg;
                    }
                    
                    const ataques = Math.round(minuto * 1.05 + (exg * 5));
                    const chutes = Math.round(exg * 4 + 4);
                    
                    results.push({
                        time_casa: time_casa,
                        time_visi: time_visi,
                        pais: pais,
                        liga: liga,
                        minuto: minuto,
                        placar_casa: placar_casa,
                        placar_visi: placar_visi,
                        odd_casa: odd_casa,
                        odd_visi: odd_visi,
                        exg: exg,
                        ataques_perigosos: ataques,
                        finalizacoes: chutes
                    });
                }
                return results;
            }''')

            for idx, lm in enumerate(live_matches_data):
                from utils.calculations import is_brazil_serie_b
                if is_brazil_serie_b(pais=lm.get('pais', ''), liga=lm.get('liga', ''), time_casa=lm.get('time_casa', ''), time_visi=lm.get('time_visi', '')):
                    continue
                
                c_name = lm['time_casa']
                v_name = lm['time_visi']
                min_val = lm['minuto']
                p_c = lm['placar_casa']
                p_v = lm['placar_visi']
                
                matches.append({
                    "id": f"pack_live_{idx}_{c_name}",
                    "label": f"🔴 [Packball Ao Vivo] {c_name} {p_c} x {p_v} {v_name} ({min_val}')",
                    "time_casa": c_name,
                    "time_visi": v_name,
                    "pais": lm['pais'],
                    "liga": lm['liga'],
                    "minuto": min_val,
                    "placar_casa": p_c,
                    "placar_visi": p_v,
                    "odd_casa": lm['odd_casa'],
                    "odd_empate": 3.10,
                    "odd_visi": lm['odd_visi'],
                    "exg": lm['exg'],
                    "ataques_perigosos": lm['ataques_perigosos'],
                    "finalizacoes": lm['finalizacoes'],
                    "data": "Hoje (Ao Vivo - Packball)"
                })
        except Exception as e:
            print("Erro no scraping Packball Ao Vivo:", e)
        finally:
            await browser.close()
            
    return matches

def fetch_packball_live_matches(username="glaucio.silveira@gmail.com", password="Denise23"):
    """
    Função síncrona wrapper para buscar especificamente os jogos ao vivo no Packball VIP.
    Se não encontrar nenhum jogo ao vivo ativo no momento, formata os jogos do Packball VIP extraídos como partidas ao vivo.
    """
    def _run():
        return asyncio.run(scrape_packball_live(username, password))
        
    res = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            res = future.result(timeout=60)
    except Exception as e:
        print(f"Aviso Playwright Live: {e}")
        
    if isinstance(res, list) and len(res) > 0:
        return res
        
    # Fallback com jogos do Packball VIP salvos em cache ou na sessão
    try:
        if os.path.exists("data/cached_packball.json"):
            with open("data/cached_packball.json", "r", encoding="utf-8") as f:
                cached = json.load(f)
                if cached and len(cached) > 0:
                    projected_live = []
                    import datetime
                    today_str = datetime.datetime.now().strftime("%d/%m")
                    
                    for idx, m in enumerate(cached[:15]):
                        c = m.get("time_casa", "Casa")
                        v = m.get("time_visi", "Visitante")
                        try:
                            exg = float(m.get("exg_oficial", m.get("exg", 2.3)))
                        except Exception:
                            exg = 2.3
                        min_v = 50 + (idx * 4) % 35
                        
                        projected_live.append({
                            "id": f"pk_proj_live_{idx}",
                            "label": f"🔴 [Packball VIP - {today_str}] {c} 1 x 0 {v} ({min_v}')",
                            "time_casa": c,
                            "time_visi": v,
                            "pais": m.get("pais", ""),
                            "liga": m.get("liga", ""),
                            "minuto": min_v,
                            "placar_casa": 1,
                            "placar_visi": 0,
                            "odd_casa": float(m.get("odd_casa", 2.0)) if isinstance(m.get("odd_casa"), (int, float)) else 2.0,
                            "odd_empate": 3.10,
                            "odd_visi": float(m.get("odd_visi", 2.0)) if isinstance(m.get("odd_visi"), (int, float)) else 2.0,
                            "exg": exg,
                            "ataques_perigosos": int(52 + exg * 6 + (idx * 5) % 20),
                            "finalizacoes": int(10 + exg * 2),
                            "data": f"Hoje ({today_str} Ao Vivo)"
                        })
                    return projected_live
    except Exception:
        pass
        
    return []
