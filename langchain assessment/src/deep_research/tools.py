import os
import time
import random


def run_search(query: str, max_results: int = 5, days: int | None = None, provider: str = "tavily") -> dict:
    if provider == "tavily":
        return run_tavily_search(query, max_results, days)
    elif provider == "exa":
        return run_exa_search(query, max_results, days)
    elif provider == "serpapi":
        return run_serpapi_search(query, max_results)
    else:
        return {"results": [], "error": f"unknown_provider_{provider}"}


def run_tavily_search(query: str, max_results: int = 5, days: int | None = None) -> dict:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return {"results": [], "error": "missing_tavily_api_key"}
    
    try:
        from tavily import TavilyClient
    except ImportError:
        return {"results": [], "error": "tavily_not_installed"}
    
    client = TavilyClient(api_key=key)
    attempt = 0
    delay = 1.0
    
    while attempt < 3:
        try:
            payload = {"query": query, "max_results": max_results, "search_depth": "advanced"}
            if days:
                payload["days"] = days
            data = client.search(**payload)
            results = data.get("results", []) if isinstance(data, dict) else []
            return {"results": results, "error": None}
        except Exception as e:
            attempt += 1
            if attempt >= 3:
                return {"results": [], "error": str(e)}
            time.sleep(delay + random.uniform(0, 0.3))
            delay *= 2
    
    return {"results": [], "error": "unknown_error"}


def run_exa_search(query: str, max_results: int = 5, days: int | None = None) -> dict:
    key = os.getenv("EXA_API_KEY")
    if not key:
        return {"results": [], "error": "missing_exa_api_key"}
    
    try:
        from exa_py import Exa
    except ImportError:
        return {"results": [], "error": "exa_not_installed"}
    
    client = Exa(api_key=key)
    attempt = 0
    delay = 1.0
    
    while attempt < 3:
        try:
            search_params = {"num_results": max_results, "use_autoprompt": True}
            if days:
                from datetime import datetime, timedelta
                start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                search_params["start_published_date"] = start_date
            
            response = client.search_and_contents(query, text=True, **search_params)
            
            results = []
            for item in response.results:
                results.append({
                    "title": getattr(item, "title", ""),
                    "url": getattr(item, "url", ""),
                    "content": getattr(item, "text", "")[:1000]
                })
            
            return {"results": results, "error": None}
        except Exception as e:
            attempt += 1
            if attempt >= 3:
                return {"results": [], "error": str(e)}
            time.sleep(delay + random.uniform(0, 0.3))
            delay *= 2
    
    return {"results": [], "error": "unknown_error"}


def run_serpapi_search(query: str, max_results: int = 5) -> dict:
    key = os.getenv("SERPAPI_API_KEY")
    if not key:
        return {"results": [], "error": "missing_serpapi_api_key"}
    
    try:
        from serpapi import GoogleSearch
    except ImportError:
        return {"results": [], "error": "serpapi_not_installed"}
    
    attempt = 0
    delay = 1.0
    
    while attempt < 3:
        try:
            params = {
                "q": query,
                "api_key": key,
                "num": max_results,
                "engine": "google"
            }
            
            search = GoogleSearch(params)
            data = search.get_dict()
            
            results = []
            for item in data.get("organic_results", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("snippet", "")
                })
            
            return {"results": results, "error": None}
        except Exception as e:
            attempt += 1
            if attempt >= 3:
                return {"results": [], "error": str(e)}
            time.sleep(delay + random.uniform(0, 0.3))
            delay *= 2
    
    return {"results": [], "error": "unknown_error"}