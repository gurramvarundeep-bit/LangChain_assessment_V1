def get_source_quality(url):
    url_lower = url.lower()
    high_quality = ["gartner.com", "mckinsey.com", "forrester.com", "bloomberg.com", 
                    "mit.edu", "stanford.edu", "harvard.edu", "nber.org", "iea.org",
                    "techcrunch.com", "technologyreview.com", "wired.com", "reuters.com"]
    low_quality = ["linkedin.com", "medium.com", "quora.com", "reddit.com"]
    
    for domain in high_quality:
        if domain in url_lower:
            return 3
    for domain in low_quality:
        if domain in url_lower:
            return 1
    return 2

def process_results(state, config):
    raw = state.get("search_results", [])
    seen = set()
    sources = []

    for item in raw:
        for r in item.get("results", []):
            url = r.get("url") or r.get("link") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            title = r.get("title") or ""
            snippet = r.get("content") or r.get("snippet") or ""
            quality = get_source_quality(url)
            sources.append({
                "title": title, 
                "url": url, 
                "snippet": snippet,
                "quality": quality
            })
    sources.sort(key=lambda x: x.get("quality", 2), reverse=True)

    lines = []
    for i, s in enumerate(sources, 1):
        title = s.get("title", "")
        url = s.get("url", "")
        snippet = s.get("snippet", "")
        lines.append(f"[{i}] {title}\n{snippet}\nurl: {url}\n")

    processed_context = "\n".join(lines)
    return {"sources": sources, "processed_context": processed_context}