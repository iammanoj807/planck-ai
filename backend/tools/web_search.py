"""Web search tool with Google and DuckDuckGo fallback"""
import json
import os


async def web_search_tool(query: str, max_results: int = 5) -> str:
    """
    Search the web using multi-provider strategy:
    1. Google Custom Search (Primary - Requires Key)
    2. DuckDuckGo Search (Fallback - Free, No Key)
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        Formatted search results
    """
    
    # 1. Try Google Search
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if google_api_key and google_cse_id:
        try:
            from tools.google_search import execute_google_search
            result = await execute_google_search(query, max_results)
            # Basic validation
            if result and not result.strip().startswith("{") and "error" not in result.lower():
                print("DEBUG: Using Google Search results")
                return result
            print("DEBUG: Google Search failed or not configured correctly, trying DuckDuckGo...")
        except Exception as e:
            print(f"DEBUG: Google Search error: {e}")

    # 2. Fallback to DuckDuckGo (Free, no keys needed)
    try:
        from tools.duckduckgo_search import execute_duckduckgo_search
        print("DEBUG: Attempting DuckDuckGo Search")
        result = await execute_duckduckgo_search(query, max_results)
        return result
    except Exception as e:
        print(f"DEBUG: DuckDuckGo Search error: {e}")
            
    # 3. If everything fails
    return json.dumps({
        "error": "All search providers failed.",
        "results": []
    })


# Tool definition for LangChain
WEB_SEARCH_TOOL_DEF = {
    "name": "web_search",
    "description": "Search the internet for current information. Use this when you need up-to-date information or facts you don't know.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 5)",
                "default": 5
            }
        },
        "required": ["query"]
    }
}
