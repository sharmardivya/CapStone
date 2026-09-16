"""
Wikipedia tools for the Destination Research Agent.

    search_wikipedia      LangChain tool the agent's LLM calls
    wikipedia_summary()   the same lookup without an LLM, used as a fallback

Calls the Wikipedia API directly with httpx and a descriptive User-Agent.
Wikipedia rate-limits unidentified clients: the `wikipedia` package (which
LangChain's WikipediaQueryRun also uses) receives HTTP 429 "too many requests"
and then fails with "Expecting value: line 1 column 1".
"""

from typing import List, Tuple

import httpx
from langchain_core.tools import tool

API_URL = "https://en.wikipedia.org/w/api.php"
# Wikipedia asks every client to identify itself with a descriptive User-Agent.
USER_AGENT = "A2A-Travel-Planner/1.0 (educational capstone project)"
MAX_ARTICLES = 2
MAX_CHARS_PER_ARTICLE = 1500  # 2 × 1,500 ≈ the 3,000-char limit the notebook used


async def fetch_wikipedia_intros(query: str, max_articles: int = MAX_ARTICLES) -> List[Tuple[str, str]]:
    """
    Search Wikipedia and return (title, introduction) for the best matches,
    most relevant first. Raises httpx errors if Wikipedia cannot be reached.
    """
    params = {
        "action": "query",
        "generator": "search",    # search for pages…
        "gsrsearch": query,
        "gsrlimit": max_articles,
        "prop": "extracts",       # …and return each page's text
        "exintro": 1,             # only the introduction section
        "explaintext": 1,         # as plain text, not HTML
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": USER_AGENT}) as client:
        response = await client.get(API_URL, params=params)
        response.raise_for_status()

    pages = response.json().get("query", {}).get("pages", {}).values()
    ranked = sorted(pages, key=lambda page: page.get("index", 0))  # "index" = search rank
    return [(page["title"], page["extract"].strip()[:MAX_CHARS_PER_ARTICLE])
            for page in ranked if page.get("extract", "").strip()]


@tool
async def search_wikipedia(query: str) -> str:
    """Look up a place on Wikipedia. Returns the introduction of the best-matching articles."""
    try:
        articles = await fetch_wikipedia_intros(query)
    except Exception as exc:
        # Report the problem as text so the agent can still answer from what it knows.
        return f"Wikipedia lookup failed for '{query}': {str(exc)[:120]}"
    if not articles:
        return f"No Wikipedia articles found for '{query}'."
    return "\n\n".join(f"Page: {title}\nSummary: {text}" for title, text in articles)


async def wikipedia_summary(destination: str, note: str = "") -> str:
    """Wikipedia introduction of `destination` without using an LLM (fallback)."""
    try:
        articles = await fetch_wikipedia_intros(destination, max_articles=1)
    except Exception as exc:
        return f"⚠️ Could not research '{destination}': {exc}"
    if not articles:
        return f"⚠️ No Wikipedia article found for '{destination}'."

    title, text = articles[0]
    suffix = f"\n\n[Note: {note}]" if note else ""
    return f"📍 {title.upper()}\n\n{text}{suffix}"
