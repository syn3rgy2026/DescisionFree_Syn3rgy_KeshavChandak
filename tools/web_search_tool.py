# OWNER: Person 2
"""
web_search_tool.py
------------------
Provides web search capabilities using DuckDuckGo (no API key required).
Returns titles, URLs, and snippets for search results.
"""

from ddgs import DDGS
from smolagents import tool


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo and return titles, URLs, and snippets.

    Use this tool to find current information, news, documentation, or any
    topic from the internet. Returns a formatted list of results with their
    source URLs.

    Args:
        query: The search query string (e.g., 'Python asyncio tutorial')
        max_results: Maximum number of results to return (default: 5, max: 10)

    Returns:
        str: Formatted search results with title, URL, and description for each
    """
    try:
        max_results = min(max_results, 10)  # Cap at 10 results

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, backend="lite"):
                results.append(r)

        if not results:
            return f"No results found for query: '{query}'"

        output_lines = [f"Search results for: '{query}'\n"]
        for i, r in enumerate(results, 1):
            title = r.get('title', 'No title')
            url = r.get('href', 'No URL')
            snippet = r.get('body', 'No description')
            output_lines.append(f"{i}. {title}")
            output_lines.append(f"   URL: {url}")
            output_lines.append(f"   {snippet}\n")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error performing web search for '{query}': {str(e)}"


@tool
def search_news(query: str, max_results: int = 5) -> str:
    """
    Search for recent news articles using DuckDuckGo News.

    Use this tool when you need current news, recent events, or up-to-date
    information about a topic.

    Args:
        query: The news search query (e.g., 'AI breakthroughs 2025')
        max_results: Maximum number of news articles to return (default: 5, max: 10)

    Returns:
        str: Formatted news results with title, URL, source, and date
    """
    try:
        max_results = min(max_results, 10)

        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append(r)


        if not results:
            return f"No news found for query: '{query}'"

        output_lines = [f"News results for: '{query}'\n"]
        for i, r in enumerate(results, 1):
            title = r.get('title', 'No title')
            url = r.get('url', 'No URL')
            snippet = r.get('body', 'No description')
            source = r.get('source', 'Unknown source')
            date = r.get('date', 'Unknown date')
            output_lines.append(f"{i}. {title}")
            output_lines.append(f"   Source: {source} | Date: {date}")
            output_lines.append(f"   URL: {url}")
            output_lines.append(f"   {snippet}\n")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error performing news search for '{query}': {str(e)}"


# Test block
if __name__ == "__main__":
    print("Testing search_web...")
    result = search_web("Python smolagents framework", max_results=3)
    print(result)
    print("\n" + "="*50 + "\n")

    print("Testing search_news...")
    result = search_news("AI agents 2025", max_results=3)
    print(result)
