import os
from tavily import TavilyClient

api_key = os.environ["TAVILY_API_KEY"]

client = TavilyClient(api_key=api_key)

response = client.search(
    query="Redmi 13 5G official specifications",
    search_depth="basic",
    include_domains=["mi.com", "xiaomi.com"],
    max_results=5,
)

print("=" * 60)
print("OFFICIAL SOURCE TEST")
print("=" * 60)

for r in response["results"]:
    print(f"Title : {r['title']}")
    print(f"URL   : {r['url']}")
    print(f"Score : {r.get('score')}")
    print("-" * 60)