# 🛒 Multi-Agent Procurement Assistant

A multi-agent AI system built with [CrewAI](https://www.crewai.com/) that autonomously searches
the web for products, scrapes and structures the data, compares candidates against a company's
requirements, and generates a professional HTML procurement report — all through a simple
Streamlit form, no code editing required.

---

## ✨ Features

- **Multi-agent pipeline** — four specialized agents collaborate sequentially, each responsible
  for one stage of the procurement workflow.
- **Real-time web search** — powered by [Tavily](https://tavily.com), finds live product listings
  across retailers and manufacturers.
- **Structured web scraping** — powered by [ScrapeGraph AI](https://scrapegraphai.com), extracts
  clean product data (price, specs, availability) from raw listing pages.
- **Automated comparison & ranking** — scores candidates against budget, specs, and stated
  priorities, with reasoning for the final recommendation.
- **Auto-generated HTML report** — a polished, shareable report with a comparison table and a
  clear top pick.
- **No-code interface** — a Streamlit form collects requirements from any user; nobody needs to
  touch the underlying code to run a new procurement request.
- **Resilient LLM routing** — uses OpenRouter's free model router, which automatically falls back
  across available free-tier models instead of depending on one that could be discontinued.

---

## 🧠 How It Works

```
User Requirements (Streamlit form)
            │
            ▼
┌────────────────────────┐
│  Product Search Agent   │  → searches the web for candidate listings
└────────────┬─────────────┘
             ▼
┌────────────────────────┐
│  Data Collection Agent  │  → scrapes each listing for price/specs/availability
└────────────┬─────────────┘
             ▼
┌────────────────────────┐
│  Procurement Analyst    │  → scores & ranks candidates against requirements
└────────────┬─────────────┘
             ▼
┌────────────────────────┐
│  Report Writer Agent    │  → generates the final HTML report
└────────────┬─────────────┘
             ▼
     📄 HTML Procurement Report
```

---

## 📸 Screenshots

<img width="1794" height="739" alt="multi_agent" src="https://github.com/user-attachments/assets/765adbd2-414b-49f8-8b2d-26bccacd1956" />

**Comparison Table**

<img width="1662" height="526" alt="analysis" src="https://github.com/user-attachments/assets/ae32ef04-3075-43fb-9910-3879185a0970" />

**Final Recommendation**

<img width="1670" height="444" alt="final rec" src="https://github.com/user-attachments/assets/d344a575-2f76-4bd3-b7a5-84399c708813" />

![Final Recommendation](final_rec.png)

---

## 🛠️ Tech Stack

| Component      | Technology                          |
|-----------------|--------------------------------------|
| Agent orchestration | [CrewAI](https://www.crewai.com/) |
| Web search      | [Tavily](https://tavily.com)         |
| Web scraping    | [ScrapeGraph AI](https://scrapegraphai.com) |
| LLM             | [OpenRouter](https://openrouter.ai) (free model router) |
| UI              | [Streamlit](https://streamlit.io)    |

---

## 🚀 Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/YOUR-USERNAME/procurement-assistant.git
   cd procurement-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys** — copy `.env.example` to `.env` and fill in your keys:
   ```
   TAVILY_API_KEY=your-tavily-key
   SGAI_API_KEY=your-scrapegraph-key
   OPENROUTER_API_KEY=your-openrouter-key
   ```
   All three offer free tiers:
   - Tavily → https://tavily.com
   - ScrapeGraph AI → https://scrapegraphai.com
   - OpenRouter → https://openrouter.ai

4. **Run the app**
   ```bash
   python -m streamlit run app.py
   ```
   The app opens at `http://localhost:8501`.

---

## 📋 Usage

1. Fill in the company name, industry, and what you need to procure.
2. Set the budget range, minimum specs, and use case.
3. List your priorities in order (e.g. value for money, reliability, warranty).
4. Click **Generate Procurement Report**.
5. Wait 1–4 minutes while the agents search, scrape, analyze, and write the report.
6. Review the generated report, including the ranked comparison table and final recommendation.

---

## ⚠️ Notes & Limitations

- Uses OpenRouter's `openrouter/free` router, which automatically selects from currently
  available free-tier models — avoids hardcoding a model that could later be paywalled or
  discontinued.
- Free-tier rate limits (requests per minute/day, across all providers) may cause occasional
  delays; the app retries automatically on rate-limit errors.
- Product data accuracy depends on what's scraped live from the web — always verify prices and
  availability before making a purchasing decision.

---

## 📄 License

This project is provided as-is for educational and portfolio purposes.
