import argparse
import requests
from app.settings import settings

parser = argparse.ArgumentParser()
parser.add_argument("workflow", choices=["aggregator", "summarizer", "all"])
args = parser.parse_args()

WEBHOOKS = {
    "aggregator": settings.N8N_WEBHOOK_ARTICLES,
    "summarizer": settings.N8N_WEBHOOK_SUMMARY,
}

targets = WEBHOOKS if args.workflow == "all" else {args.workflow: WEBHOOKS[args.workflow]}

for name, url in targets.items():
    if not url:
        print(f"SKIP {name}: webhook not configured")
        continue
    r = requests.get(url)
    r.raise_for_status()
    print(f"OK: {name}")