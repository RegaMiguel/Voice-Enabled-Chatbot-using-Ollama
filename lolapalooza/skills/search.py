import logging
from duckduckgo_search import DDGS

logger = logging.getLogger("thursday.skills.search")

MAX_RESULTS = 4

def search(query: str) -> str:
    logger.info(f"Web search: '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=MAX_RESULTS))

        if not results:
            return "No results found for the query."
        
        lines = [f"Web search: '{query}'"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "No snippet")
            href = r.get("href", "")
            lines.append(f"{i}. {title}\n {body}\n  Source: {href}")

        return "\n\n".join(lines)
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Search failed: {e}"
    
def is_search_query(text: str) -> bool:
    triggers = [
        "search", "look up", "look up", "find out", "what is",
        "who is", "when did", "where is", "how do", "latest",
        "news", "current", "today", "price of", "weather in",
    ]

    lower = text.lower()
    return any(t in lower for t in triggers)