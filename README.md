# ⚽ Múltiplas Seguras - Sistema de Apostas Esportivas Inteligentes

Aplicação completa em Python / Streamlit para análise estatística, gerenciamento de bancas, simulação de bilhetes e extração automatizada de dados VIP do **Packball**.

---

## 🚀 Funcionalidades Principais

1. **🌐 Integração Packball VIP (7 Dias):**
   - Extração automatizada e autenticada com navegação pelos próximos 7 dias.
   - Filtro inteligente pela coluna `FAV` (*Sem favorito ou leve favoritismo*).
   - Captura de dados oficiais nativos:
     - 🎯 **ExG (Expectativa de Gols da Partida)**
     - ⚽ **Ambas Marcam (BTS %)**
     - 🏆 **Probabilidade de Vitória (% Win)**
     - 📈 **PPG (Pontos por Jogo)**
     - 🚩 **Média de Escanteios (AVG)** e **Expectativa de Escanteios (ExC)**
     - 🛡️ **Poder e Solidez Defensiva**

2. **🎫 Simulador de Bilhetes & Múltiplas:**
   - Criação de bilhetes com cálculo automático de Odds acumuladas, Retorno Potencial e Probabilidade Implícita.
   - Integração direta com os jogos aprovados do Packball (sugestão de Handicap Europeu +3 para o Underdog).
   - Exportação em PDF e formato de texto para compartilhamento.

3. **📈 Projeto de Alavancagem:**
   - Planejamento de ciclos de alavancagem com metas diárias, controle de perdas e gráficos de projeção.

4. **⚡ Monitoramento Ao Vivo & Gestão:**
   - Acompanhamento de partidas, histórico de bilhetes e relatórios.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Frontend / UI:** [Streamlit](https://streamlit.io/)
- **Web Scraping & Automação:** [Playwright](https://playwright.dev/python/)
- **Análise de Dados:** Pandas / NumPy
- **Relatórios:** ReportLab (Geração de PDFs)

---

## 📦 Como Executar o Projeto

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com/glau234/Multiplas_Seguras.git
   cd Multiplas_Seguras
   ```

2. **Instalar Dependências:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Iniciar a Aplicação:**
   ```bash
   streamlit run app.py
   ```
