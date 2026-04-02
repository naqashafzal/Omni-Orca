"""
web_search_agent.py
Gives the Agent Swarm real-time internet access via DuckDuckGo (no API key needed).
"""

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WebSearchAgent:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        }

    def search(self, query: str, max_results: int = 5) -> str:
        """
        Performs a real-time DuckDuckGo web search.
        Returns a formatted string of results with titles, URLs, and snippets.
        """
        if not DDGS_AVAILABLE:
            return "Error: duckduckgo-search not installed. Run: pip install duckduckgo-search"

        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(r)

            if not results:
                return f"No results found for: '{query}'"

            output = f"Search results for: '{query}'\n\n"
            for i, r in enumerate(results, 1):
                output += f"[{i}] {r.get('title', 'No Title')}\n"
                output += f"    URL: {r.get('href', '')}\n"
                output += f"    {r.get('body', '')[:300]}...\n\n"

            return output.strip()

        except Exception as e:
            return f"Web search error: {e}"

    def fetch_page_text(self, url: str, max_chars: int = 3000) -> str:
        """
        Fetches readable plain text from a web URL (strips all HTML/CSS/JS).
        Perfect for the agent to read an article or research page.
        """
        if not BS4_AVAILABLE:
            return "Error: beautifulsoup4 not installed. Run: pip install beautifulsoup4"

        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove script and style bulk
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Remove excessive blank lines
            lines = [l for l in text.splitlines() if l.strip()]
            clean_text = "\n".join(lines)

            return clean_text[:max_chars] + "..." if len(clean_text) > max_chars else clean_text

        except Exception as e:
            return f"Page fetch error for {url}: {e}"

    def search_news(self, query: str, max_results: int = 5) -> str:
        """Fetches latest news articles on a topic."""
        if not DDGS_AVAILABLE:
            return "Error: duckduckgo-search not installed."

        try:
            output = f"Latest news for: '{query}'\n\n"
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=max_results):
                    output += f"• {r.get('title', '')}\n"
                    output += f"  Source: {r.get('source', '')} | {r.get('date', '')}\n"
                    output += f"  {r.get('body', '')[:200]}...\n\n"
            return output.strip()
        except Exception as e:
            return f"News search error: {e}"


# Standalone test
if __name__ == "__main__":
    agent = WebSearchAgent()
    print("=== Testing Web Search ===")
    print(agent.search("gold price today Pakistan"))
    print("\n=== Testing News Search ===")
    print(agent.search_news("AI news today"))
