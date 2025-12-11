"""Google Custom Search API integration for Planck AI"""
import os
import json
import httpx


async def execute_google_search(query: str, count: int = 5) -> str:
    """
    Execute a search using Google Custom Search API.
    
    Requires:
    - GOOGLE_API_KEY: Your Google Cloud API key
    - GOOGLE_CSE_ID: Your Custom Search Engine ID
    
    Returns formatted search results with titles, snippets, and URLs.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        print("DEBUG: Missing GOOGLE_API_KEY or GOOGLE_CSE_ID")
        return json.dumps({
            "error": "Google Search not configured. Missing GOOGLE_API_KEY or GOOGLE_CSE_ID."
        })
    
    print(f"DEBUG: Starting Google Search for '{query}'")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": min(count, 10)  # Max 10 per request
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 429:
                return json.dumps({"error": "Google API rate limit exceeded (100/day free tier)"})
            
            if response.status_code != 200:
                return json.dumps({"error": f"Google API error: {response.status_code}"})
            
            data = response.json()
            
            # Format results like Perplexity would see them
            results = []
            items = data.get("items", [])
            
            for item in items:
                result = {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),  # This is the key snippet!
                    "url": item.get("link", "")
                }
                results.append(result)
                
            # Format as readable text for the LLM
            formatted = []
            for r in results:
                formatted.append(
                    f"Title: {r['title']}\n"
                    f"Description: {r['snippet']}\n"
                    f"URL: {r['url']}"
                )
            
            output = "\n\n".join(formatted)
            print(f"DEBUG: Google Search success. Found {len(results)} results.")
            return output
            
    except Exception as e:
        print(f"DEBUG: Google Search error: {e}")
        return json.dumps({"error": str(e)})
