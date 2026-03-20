#!/usr/bin/env python3
"""
synthesize.py — Structure research into newsletter content via Claude.

Usage:
    python tools/synthesize.py
    python tools/synthesize.py --tone analytical --length medium

Reads:  .tmp/research_raw.json
Output: .tmp/newsletter_content.json
"""

import argparse
import json
import os
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
STYLE_CONFIG = "config/newsletter_style.json"
INPUT_PATH = ".tmp/research_raw.json"
OUTPUT_PATH = ".tmp/newsletter_content.json"


def load_model() -> str:
    with open(STYLE_CONFIG) as f:
        return json.load(f).get("model", "google/gemini-2.0-flash-exp:free")

SYSTEM_PROMPT = """You are an expert newsletter writer. Your job is to take raw research and structure it into a compelling, well-organized newsletter.

You must respond with ONLY valid JSON matching this exact schema — no markdown, no explanation, just the JSON object:

{
  "headline": "Compelling, specific headline (max 12 words)",
  "subheadline": "One sentence that expands on the headline with a key insight",
  "summary": "Two sentences: what happened and why it matters",
  "sections": [
    {
      "heading": "Section heading",
      "body": "2-3 paragraphs of well-written prose. Each paragraph is a separate string joined with \\n\\n",
      "citation_indexes": [1, 2]
    }
  ],
  "key_stats": [
    {
      "label": "Short descriptive label (max 6 words)",
      "value": "The statistic (e.g. '$4.2B', '73%', '2.1x')",
      "citation_index": 1
    }
  ],
  "infographic_suggestions": [
    {
      "type": "bar_chart|line_chart|pie_chart|stat_card|illustration",
      "title": "Chart or card title",
      "data": {},
      "prompt": "For illustrations: detailed Gemini Imagen prompt. For charts/cards: leave empty string."
    }
  ]
}

RULES:
- sections: 3-4 sections, each with substantive content
- key_stats: 2-4 stats, each MUST have a citation_index that exists in the citations array. Never invent statistics.
- infographic_suggestions: include 2-4 items mixing charts, stat_cards, and 1 illustration
  - illustration: prompt field must be a vivid, detailed visual scene relevant to the topic (no text/numbers in image). data field = {}
  - bar_chart/line_chart/pie_chart: data field must contain {"labels": [...], "values": [...], "unit": "..."}
  - stat_card: data field must contain {"value": "...", "label": "..."}
- citation_indexes in sections: list which citation indexes support that section
- All prose must be engaging, clear, and written for a general intelligent audience"""


def synthesize(tone: str = "analytical", length: str = "medium") -> dict:
    if not OPENROUTER_API_KEY:
        sys.exit("Error: OPENROUTER_API_KEY not set in .env")

    if not os.path.exists(INPUT_PATH):
        sys.exit(f"Error: {INPUT_PATH} not found. Run research.py first.")

    with open(INPUT_PATH) as f:
        research = json.load(f)

    length_instructions = {
        "short": "Keep sections concise — 1-2 paragraphs each. Target ~400 words total.",
        "medium": "Write thorough sections — 2-3 paragraphs each. Target ~700 words total.",
        "long": "Write detailed sections — 3-4 paragraphs each. Target ~1000 words total.",
    }

    tone_instructions = {
        "analytical": "Tone: analytical and data-driven. Lead with evidence.",
        "casual": "Tone: conversational and accessible. Use plain language.",
        "executive": "Tone: executive briefing style. Lead with implications and decisions.",
    }

    user_prompt = f"""Topic: {research['topic']}

{tone_instructions.get(tone, tone_instructions['analytical'])}
{length_instructions.get(length, length_instructions['medium'])}

Research summary:
{research['summary']}

Available citations (use these index numbers in your response):
{json.dumps(research['citations'], indent=2)}

Structure this into a newsletter. Remember: every key_stat MUST reference a citation_index from the list above."""

    model = load_model()
    print(f"Synthesizing newsletter content (model: {model}, tone: {tone}, length: {length})...")

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()

    try:
        content = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Warning: Model returned invalid JSON. Attempting to extract JSON block...")
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            content = json.loads(match.group())
        else:
            sys.exit(f"Error: Could not parse response as JSON.\n{e}\n\nRaw response:\n{raw[:500]}")

    valid_citation_indexes = {c["index"] for c in research["citations"]}
    invalid_stats = [
        s for s in content.get("key_stats", [])
        if s.get("citation_index") not in valid_citation_indexes
    ]
    if invalid_stats:
        print(f"Warning: {len(invalid_stats)} stat(s) have invalid citation indexes and were removed:")
        for s in invalid_stats:
            print(f"  - {s['label']}: {s['value']} (citation_index: {s.get('citation_index')})")
        content["key_stats"] = [
            s for s in content.get("key_stats", [])
            if s.get("citation_index") in valid_citation_indexes
        ]

    content["topic"] = research["topic"]
    content["citations"] = research["citations"]
    content["retrieved_at"] = research["retrieved_at"]

    os.makedirs(".tmp", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(content, f, indent=2)

    print(f"\nSynthesis complete:")
    print(f"  Headline: {content.get('headline', 'N/A')}")
    print(f"  Sections: {len(content.get('sections', []))}")
    print(f"  Key stats: {len(content.get('key_stats', []))}")
    print(f"  Infographic suggestions: {len(content.get('infographic_suggestions', []))}")
    print(f"Output: {OUTPUT_PATH}")
    return content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthesize research into newsletter content")
    parser.add_argument(
        "--tone",
        choices=["analytical", "casual", "executive"],
        default="analytical",
        help="Writing tone (default: analytical)",
    )
    parser.add_argument(
        "--length",
        choices=["short", "medium", "long"],
        default="medium",
        help="Newsletter length (default: medium)",
    )
    args = parser.parse_args()
    synthesize(args.tone, args.length)
