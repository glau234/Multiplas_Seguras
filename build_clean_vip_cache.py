import asyncio
from playwright.async_api import async_playwright
import json
import os

async def build_clean_vip_cache(email, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1400, 'height': 900})
        page = await context.new_page()
        
        print("1. Logging into Packball VIP...")
        await page.goto("https://packball.com/pt/login", wait_until="domcontentloaded")
        await page.wait_for_selector('input[name="email"]')
        await page.fill('input[name="email"]', email)
        await page.fill('input[name="password"]', password)
        await page.click('.btn-login button, button:has-text("Entrar")')
        await page.wait_for_timeout(4000)
        
        if not page.url.endswith("/matches"):
            await page.goto("https://packball.com/pt/matches")
        await page.wait_for_timeout(4000)
        
        all_matches = []
        seen = set()
        
        for day in range(7):
            current_date = await page.evaluate("() => document.querySelector('.arrow-nav .title-active')?.innerText.trim() || ''")
            if not current_date:
                current_date = f"Dia {day+1}"
            print(f"Buscando {current_date} (Passo {day+1}/7)...")
            
            day_matches = await page.evaluate(r'''() => {
                const rows = Array.from(document.querySelectorAll('ul.row'));
                const results = [];
                
                for (const row of rows) {
                    const html = row.innerHTML;
                    
                    const teamHomes = Array.from(row.querySelectorAll('.team-name-home .team-home'));
                    const teamAways = Array.from(row.querySelectorAll('.team-name-away .team-away'));
                    if (teamHomes.length === 0 || teamAways.length === 0) continue;
                    
                    const time_casa = teamHomes[0].textContent.trim();
                    const time_visi = teamAways[0].textContent.trim();
                    
                    const countryEl = row.querySelector('.short-country');
                    const leagueEl = row.querySelector('.title-league span');
                    const timeEl = row.querySelector('.time time');
                    
                    const pais = countryEl ? countryEl.textContent.trim() : '';
                    const liga = leagueEl ? leagueEl.textContent.trim() : '';
                    const horario = timeEl ? timeEl.textContent.trim() : '';
                    
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
                    
                    const is_hollow_star = html.includes('Sem favorito') || 
                                           html.includes('leve favoritismo') || 
                                           row.querySelector('li.col.custom.b3.tt i.default') !== null;
                    
                    const customCols = Array.from(row.querySelectorAll('li.col.custom'));
                    let win_prob = '';
                    let ppg = '';
                    let gols_avg = '';
                    let exg = 2.2;
                    let over25 = '';
                    let bts = '';
                    let escanteios_avg = '8.5';
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
                    if (customCols.length >= 11) {
                        const c10 = customCols[10].innerText.trim();
                        if (c10) escanteios_avg = c10;
                    }
                    if (customCols.length >= 12) {
                        const c11 = customCols[11].innerText.trim();
                        if (c11) escanteios_exc = c11;
                    }
                    
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
                from utils.calculations import is_brazil_serie_b
                if is_brazil_serie_b(pais=m.get('pais', ''), liga=m.get('liga', ''), time_casa=m.get('time_casa', ''), time_visi=m.get('time_visi', '')):
                    continue
                    
                k = f"{current_date}_{m['time_casa']}_{m['time_visi']}"
                if k not in seen:
                    seen.add(k)
                    all_matches.append({
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
                    
            try:
                await page.locator('.arrow-nav .arrow-next, .arrow-next').click()
                await page.wait_for_timeout(3500)
            except Exception as e:
                print("Fim das datas:", e)
                break
                
        from utils.calculations import filter_out_serie_b
        all_matches = filter_out_serie_b(all_matches)
        os.makedirs("data", exist_ok=True)
        with open("data/cached_packball.json", "w", encoding="utf-8") as f:
            json.dump(all_matches, f, indent=2, ensure_ascii=False)
            
        print(f"Sucesso! Salvas {len(all_matches)} partidas VIP com métricas de escanteios corretas!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(build_clean_vip_cache("glaucio.silveira@gmail.com", "Denise23"))
