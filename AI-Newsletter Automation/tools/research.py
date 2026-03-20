#!/usr/bin/env python3
"""
research.py — Newsletter research via Perplexity API.

Usage:
    python tools/research.py "your topic here"
    python tools/research.py "your topic here" --recency month

Output: .tmp/research_raw.json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OUTPUT_PATH = ".tmp/research_raw.json"
MIN_CITATIONS = 3


def fetch_page_title(url: str) -> str:
    """Fetch the HTML <title> of a URL. Returns None on failure."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsletterBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        match = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            # Clean up common suffixes like " | Site Name" or " - Site Name"
            title = re.sub(r"\s*[\|–—-]\s*.{3,40}$", "", title).strip()
            return title[:120] if title else None
    except Exception:
        pass
    return None


def research(topic: str, recency: str = "month") -> dict:
    if not PERPLEXITY_API_KEY:
        sys.exit("Error: PERPLEXITY_API_KEY not set in .env")

    client = OpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai",
    )

    prompt = (
        f"Research the following topic thoroughly and provide a comprehensive overview: {topic}\n\n"
        "Include:\n"
        "- The latest developments and news\n"
        "- Key statistics and data points (with specific numbers)\n"
        "- Expert opinions or notable quotes\n"
        "- Background context and significance\n"
        "- Future implications or trends\n\n"
        "Cite your sources inline using [1], [2], etc. format."
    )

    print(f"Researching: {topic}")
    print(f"Recency filter: {recency}")

    response = client.chat.completions.create(
        model="sonar",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a thorough research assistant. Provide detailed, factual information "
                    "with specific statistics, data points, and expert insights. Always cite sources."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        extra_body={"search_recency_filter": recency},
    )

    message = response.choices[0].message
    content = message.content

    citations_raw = getattr(response, "citations", None) or []

    citations = []
    for i, url in enumerate(citations_raw, start=1):
        domain = url.split("/")[2] if url.startswith("http") else url
        title = fetch_page_title(url) or domain
        citations.append({
            "index": i,
            "url": url,
            "source_domain": domain,
            "title": title,
        })

    if len(citations) < MIN_CITATIONS:
        print(
            f"Warning: Only {len(citations)} citations returned (minimum {MIN_CITATIONS}). "
            "Consider retrying with a broader query."
        )

    result = {
        "topic": topic,
        "retrieved_at": datetime.utcnow().isoformat() + "Z",
        "recency_filter": recency,
        "summary": content,
        "citations": citations,
        "citation_count": len(citations),
    }

    os.makedirs(".tmp", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResearch complete: {len(citations)} citations found")
    print(f"Output: {OUTPUT_PATH}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research a topic via Perplexity API")
    parser.add_argument("topic", help="Topic to research")
    parser.add_argument(
        "--recency",
        choices=["day", "week", "month", "year"],
        default="month",
        help="Recency filter for search results (default: month)",
    )
    args = parser.parse_args()
    research(args.topic, args.recency)
