"""DuckDuckGo Search integration for Planck AI"""
import json
from duckduckgo_search import DDGS

async def execute_duckduckgo_search(query: str, count: int = 5) -> str:
    """
    Execute a search using DuckDuckGo (Free, no API key required).
    
    Returns formatted search results with titles, snippets, and URLs.
    """
    print(f"DEBUG: Starting DuckDuckGo Search for '{query}'")
    
    try:
        # DDGS is synchronous but fast enough for this use case, 
        # or we could run it in an executor if needed.
        # duckduckgo_search library handles the scraping efficiently.
        with DDGS() as ddgs:
            # Revert to default params to fix empty results
            results = list(ddgs.text(query, max_results=count))
            
        if not results:
            print("DEBUG: DuckDuckGo returned no results")
            return json.dumps({"results": []})
            
        # Format as readable text for the LLM
        formatted = []
        for r in results:
            title = r.get('title', '')
            snippet = r.get('body', '') # DDG uses 'body' for snippet
            url = r.get('href', '')
            
            formatted.append(
                f"Title: {title}\n"
                f"Description: {snippet}\n"
                f"URL: {url}"
            )
        
        output = "\n\n".join(formatted)
        print(f"DEBUG: DuckDuckGo Search success. Found {len(results)} results.")
        return output
            
    except Exception as e:
        print(f"DEBUG: DuckDuckGo Search error: {e}")
        return json.dumps({"error": f"DuckDuckGo error: {str(e)}"})
