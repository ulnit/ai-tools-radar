#!/usr/bin/env python3
"""AI Tools Radar - Weekly scraper. Stdlib only, no pip needed."""
import json, gzip, urllib.request, datetime, os, sys

DATA_DIR = os.path.expanduser("~/products/ai-tools-radar/data")
os.makedirs(DATA_DIR, exist_ok=True)

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header('User-Agent', 'AI-Tools-Radar/1.0')
    req.add_header('Accept', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            if r.headers.get('Content-Encoding') == 'gzip':
                data = gzip.decompress(data)
            return json.loads(data)
    except Exception as e:
        return {"error": str(e), "source": url}

results = {"fetched_at": datetime.datetime.now().isoformat(), "rounds": []}

# GitHub Trending
gh = fetch("https://api.github.com/search/repositories?q=stars:>50+created:>7days&sort=stars&order=desc&per_page=10")
if "items" in gh:
    results["rounds"].append({
        "source": "GitHub Trending (7 days)",
        "items": [{"name": r["full_name"], "stars": r["stargazers_count"],
                    "desc": r.get("description",""), "url": r["html_url"],
                    "lang": r.get("language",""), "topics": r.get("topics",[])}
                  for r in gh["items"]]
    })

# Hacker News
hn = fetch("https://hn.algolia.com/api/v1/search?query=AI+tool+agent+automation&tags=story&hitsPerPage=10")
if "hits" in hn:
    results["rounds"].append({
        "source": "Hacker News",
        "items": [{"title": h["title"], "url": h.get("url",""), "points": h.get("points",0),
                    "comments": h.get("num_comments",0)} for h in hn["hits"] if h.get("points",0) > 3]
    })

# Dev.to
devto = fetch("https://dev.to/api/articles?tag=ai&top=7&per_page=5")
if isinstance(devto, list):
    results["rounds"].append({
        "source": "Dev.to AI",
        "items": [{"title": a["title"], "url": a["url"], "reactions": a.get("positive_reactions_count",0),
                    "comments": a.get("comments_count",0), "author": a["user"]["username"]}
                  for a in devto[:5]]
    })

# Reddit
reddit = fetch("https://www.reddit.com/r/MachineLearning/hot.json?limit=10",
               {"User-Agent": "AI-Tools-Radar/1.0"})
if "data" in reddit:
    posts = reddit["data"]["children"]
    results["rounds"].append({
        "source": "Reddit r/MachineLearning",
        "items": [{"title": p["data"]["title"], "ups": p["data"]["ups"],
                    "comments": p["data"]["num_comments"], "url": p["data"]["url"]}
                  for p in posts if p["data"]["ups"] > 3]
    })

date_str = datetime.datetime.now().strftime("%Y-%m-%d")
path = f"{DATA_DIR}/radar-{date_str}.json"
with open(path, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

total = sum(len(r.get("items",[])) for r in results["rounds"])
print(f"✅ Scraped {len(results['rounds'])} sources, {total} items → {path}")