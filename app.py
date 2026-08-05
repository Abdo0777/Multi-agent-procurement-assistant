import os
import re
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg

from tavily import TavilyClient
from scrapegraph_py import Client
from crewai.tools import tool
from crewai import Agent, Task, Crew, Process, LLM

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
sgai_client = Client(api_key=os.environ["SGAI_API_KEY"])


@tool("Web Search")
def search_tool(query: str) -> str:
    """Searches the web for the given query using Tavily and returns titles, URLs, and short snippets."""
    response = tavily_client.search(query=query, max_results=3)
    results = response.get("results", [])
    formatted = "\n".join(
        f"- {r['title']}: {r['url']}\n  {r.get('content', '')[:120]}"
        for r in results
    )
    return formatted or "No results found."


@tool("Scrape Product Page")
def scrape_tool(url: str) -> str:
    """Scrapes a product URL and extracts product name, price, specs, and availability."""
    response = sgai_client.smartscraper(
        website_url=url,
        user_prompt=(
            "Extract only the single most relevant product: name, price, "
            "key specs (CPU/RAM/storage), and availability. Be extremely concise."
        ),
    )
    result = response.get("result") if isinstance(response, dict) else str(response)
    return str(result)[:1200]


llm = LLM(
    model="openrouter/openrouter/free",
    api_key=os.environ["OPENROUTER_API_KEY"],
    max_retries=3,
    temperature=0.3,
)

search_agent = Agent(
    role="Product Search Specialist",
    goal="Find relevant product listing pages that match the company's procurement requirements",
    backstory=(
        "You are an expert at finding product options online. Given a company's "
        "requirements, you search the web and identify the most promising product "
        "listing URLs from retailers and manufacturers."
    ),
    tools=[search_tool],
    llm=llm,
    verbose=False,
    max_iter=8,
    allow_delegation=False,
)

scraper_agent = Agent(
    role="Data Collection Specialist",
    goal="Extract accurate structured product data (price, specs, availability) from listing pages",
    backstory=(
        "You are skilled at scraping and extracting clean, structured data from "
        "messy web pages. You take URLs found by the search specialist and pull out "
        "exact prices, specifications, and availability info."
    ),
    tools=[scrape_tool],
    llm=llm,
    verbose=False,
    max_iter=8,
    allow_delegation=False,
)

analyst_agent = Agent(
    role="Procurement Analyst",
    goal="Compare and rank scraped products based on price, specs, and value for the company's needs",
    backstory=(
        "You are a meticulous procurement analyst. You compare products against the "
        "company's budget and requirements, score them on value for money, reliability, "
        "and fit, then rank them with clear justification."
    ),
    llm=llm,
    verbose=False,
    max_iter=8,
    allow_delegation=False,
)

report_agent = Agent(
    role="Report Writer",
    goal="Generate a clear, professional HTML procurement report with recommendations",
    backstory=(
        "You are a business writer who turns analysis into polished, decision-ready "
        "reports. You produce clean HTML reports summarizing findings and top recommendations."
    ),
    llm=llm,
    verbose=False,
    max_iter=8,
    allow_delegation=False,
)


def _extract_wait_seconds(error_text: str, default: float = 25.0) -> float:
    """Parses Groq's 'Please try again in 20.29s' message; falls back to a default wait."""
    match = re.search(r"try again in ([\d.]+)s", error_text)
    if match:
        return float(match.group(1)) + 2
    return default


def run_crew_with_retry(crew, max_attempts=4):
    """Retries a crew run, waiting out Groq's rate-limit cooldown when hit."""
    last_error = None
    for attempt in range(max_attempts):
        try:
            return crew.kickoff()
        except Exception as e:
            last_error = e
            error_text = str(e)
            if "rate_limit" in error_text.lower() or "RateLimitError" in error_text:
                wait_time = _extract_wait_seconds(error_text)
                time.sleep(wait_time)
            else:
                time.sleep(3)
    raise last_error


def run_procurement(company_name, industry, need, budget_min, budget_max,
                     min_ram, min_storage, cpu_pref, use_case, priorities):
    dynamic_context = f"""
Company: {company_name}
Industry: {industry}

Current Need:
{need}

Requirements:
- Budget: ${budget_min} - ${budget_max} per unit
- Minimum specs: {min_ram}GB RAM, {min_storage}GB SSD, {cpu_pref}
- Use case: {use_case}

Priorities (in order):
{priorities}
"""

    dyn_search_task = Task(
        description=(
            f"Based on this company context:\n{dynamic_context}\n\n"
            "Search the web for product listing pages that match the requirements. "
            "Find at least 4-5 candidate product URLs from different retailers/manufacturers. "
            "Search one query at a time, do not attempt multiple searches simultaneously."
        ),
        expected_output="A list of 4-5 candidate product URLs with the retailer/site name for each.",
        agent=search_agent,
    )

    dyn_scrape_task = Task(
        description=(
            "Using the candidate URLs found in the previous task, scrape each product page "
            "to extract: product name, price, key specifications, and availability. "
            "Scrape one URL at a time, do not attempt multiple scrapes simultaneously."
        ),
        expected_output=(
            "A structured list of scraped products, each with name, price, specs, "
            "availability, and source URL."
        ),
        agent=scraper_agent,
        context=[dyn_search_task],
    )

    dyn_analysis_task = Task(
        description=(
            f"Given the company context:\n{dynamic_context}\n\n"
            "Compare the scraped products against the requirements using ONLY data explicitly "
            "present in the scraped results — do not invent prices or specs. Score each product on "
            "value for money, spec fit, and reliability. Rank them from best to worst with clear reasoning."
        ),
        expected_output=(
            "A ranked list of products with scores and short justification for each, "
            "plus a clear top recommendation."
        ),
        agent=analyst_agent,
        context=[dyn_scrape_task],
    )

    dyn_report_task = Task(
        description=(
            "Using the ranked comparison, write a complete, professional HTML procurement "
            "report. Include: title, company context summary, a comparison table of all "
            "products (name, price, specs, score), and a final recommendation section with "
            "reasoning. Return ONLY valid HTML — no markdown, no code fences."
        ),
        expected_output="A complete standalone HTML document as a string.",
        agent=report_agent,
        context=[dyn_analysis_task],
    )

    dyn_crew = Crew(
        agents=[search_agent, scraper_agent, analyst_agent, report_agent],
        tasks=[dyn_search_task, dyn_scrape_task, dyn_analysis_task, dyn_report_task],
        process=Process.sequential,
        max_rpm=8,
        verbose=False,
    )

    dyn_result = run_crew_with_retry(dyn_crew)

    html_output = str(dyn_result)
    if html_output.strip().startswith("```"):
        html_output = html_output.strip().strip("`")
        if html_output.lower().startswith("html"):
            html_output = html_output[4:].strip()

    # Force a readable light background regardless of what the LLM generated
    styled_output = f"""
    <html>
    <head>
        <style>
            body {{
                background-color: #ffffff;
                color: #000000;
                font-family: Arial, sans-serif;
                padding: 20px;
            }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            th {{ background-color: #f0f0f0; }}
        </style>
    </head>
    <body>
        {html_output}
    </body>
    </html>
    """

    return styled_output


st.set_page_config(page_title="Procurement Assistant", layout="wide")
st.title("🛒 Multi-Agent Procurement Assistant")
st.write("Fill in your requirements and get an AI-generated procurement report.")

col1, col2 = st.columns(2)
company_name = col1.text_input("Company Name", "TechNova Solutions")
industry = col2.text_input("Industry", "Software Development / IT Services")

need = st.text_input("What do you need to buy?", "10 laptops for our new development team")

col3, col4 = st.columns(2)
budget_min = col3.number_input("Min Budget ($)", value=800)
budget_max = col4.number_input("Max Budget ($)", value=1200)

col5, col6, col7 = st.columns(3)
min_ram = col5.number_input("Min RAM (GB)", value=16)
min_storage = col6.number_input("Min Storage (GB)", value=512)
cpu_pref = col7.text_input("CPU Preference", "Intel i7 or AMD Ryzen 7")

use_case = st.text_input("Use Case", "Software development, occasional light video editing")
priorities = st.text_area(
    "Priorities (in order)",
    "1. Value for money\n2. Reliability / brand reputation\n3. Warranty/support\n4. Delivery time",
)

if st.button("Generate Procurement Report", type="primary"):
    with st.spinner("Running agents — this can take 1-4 minutes (may pause briefly if rate-limited)..."):
        try:
            html_output = run_procurement(
                company_name, industry, need, budget_min, budget_max,
                min_ram, min_storage, cpu_pref, use_case, priorities,
            )
            st.components.v1.html(html_output, height=800, scrolling=True)
        except Exception as e:
            st.error(f"Something went wrong: {e}")