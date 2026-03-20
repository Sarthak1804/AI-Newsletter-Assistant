#!/usr/bin/env python3
"""
render_html.py — Generate a fully themed HTML newsletter.
Each theme has its own fonts, layout structure, decorative elements, and imagery style.
"""

import base64
import json
import os
import re
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

CONTENT_PATH = ".tmp/newsletter_content.json"
MANIFEST_PATH = ".tmp/infographics/manifest.json"
OUTPUT_PATH = ".tmp/newsletter_final.html"
STYLE_CONFIG = "config/newsletter_style.json"


# ── THEME REGISTRY ─────────────────────────────────────────────────────────────
THEMES = {
    "travel": {
        "keywords": ["travel", "tourism", "gulmarg", "kashmir", "himalaya", "mountain",
                     "beach", "nature", "scenic", "valley", "glacier", "forest",
                     "national park", "destination", "trek", "wildlife", "landscape"],
        "layout": "travel",
        "unsplash_query": None,  # filled from topic
        "accent": "#C0392B",
        "accent2": "#E67E22",
        "page_bg": "#FAFAF7",
        "footer_bg": "#1C1C1C",
        "hero_overlay": "rgba(0,0,0,0.45)",
        "fonts": "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Lato:wght@300;400;700&family=Playfair+Display+SC:wght@700&display=swap",
        "heading_font": "'Playfair Display', Georgia, serif",
        "body_font": "'Lato', sans-serif",
        "mono_font": "Georgia, serif",
    },
    "eco": {
        "keywords": ["ev", "electric vehicle", "solar", "climate", "sustainability",
                     "green", "renewable", "environment", "energy", "carbon",
                     "clean energy", "wind", "battery", "emission"],
        "layout": "eco",
        "accent": "#27AE60",
        "accent2": "#F39C12",
        "page_bg": "#F0F7F2",
        "footer_bg": "#1B4332",
        "fonts": "https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap",
        "heading_font": "'DM Sans', sans-serif",
        "body_font": "'DM Sans', sans-serif",
        "mono_font": "'DM Mono', monospace",
    },
    "finance": {
        "keywords": ["stock", "market", "finance", "economy", "gdp", "inflation",
                     "banking", "investment", "crypto", "bitcoin", "trade",
                     "recession", "startup", "ipo", "funding", "revenue", "interest rate"],
        "layout": "finance",
        "accent": "#B8860B",
        "accent2": "#2471A3",
        "page_bg": "#FDFCF8",
        "footer_bg": "#0A1628",
        "fonts": "https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap",
        "heading_font": "'IBM Plex Serif', Georgia, serif",
        "body_font": "'IBM Plex Sans', sans-serif",
        "mono_font": "'IBM Plex Mono', monospace",
    },
    "health": {
        "keywords": ["health", "medical", "biotech", "pharma", "cancer", "drug",
                     "hospital", "wellness", "mental health", "vaccine", "genomics",
                     "longevity", "nutrition", "fitness", "disease", "clinical"],
        "layout": "health",
        "accent": "#0E86D4",
        "accent2": "#E74C3C",
        "page_bg": "#F7FBFF",
        "footer_bg": "#0A2540",
        "fonts": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Roboto+Mono:wght@400;500&display=swap",
        "heading_font": "'Inter', sans-serif",
        "body_font": "'Inter', sans-serif",
        "mono_font": "'Roboto Mono', monospace",
    },
    "tech": {
        "keywords": ["artificial intelligence", "software", "machine learning",
                     "llm", "robotics", "semiconductor", "chip", "cloud", "saas",
                     "cybersecurity", "space", "quantum", "agentic", "agent",
                     "neural", "deep learning", "generative"],
        "layout": "tech",
        "accent": "#E8622A",
        "accent2": "#F4D03F",
        "page_bg": "#F5F5F0",
        "footer_bg": "#0D0D0D",
        "fonts": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700;800&family=Space+Mono:wght@400;700&display=swap",
        "heading_font": "'Space Grotesk', sans-serif",
        "body_font": "'Space Grotesk', sans-serif",
        "mono_font": "'Space Mono', monospace",
    },
    "default": {
        "keywords": [],
        "layout": "tech",
        "accent": "#E94560",
        "accent2": "#F4D03F",
        "page_bg": "#F5F5F0",
        "footer_bg": "#1A1A2E",
        "fonts": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700;800&family=Space+Mono:wght@400;700&display=swap",
        "heading_font": "'Space Grotesk', sans-serif",
        "body_font": "'Space Grotesk', sans-serif",
        "mono_font": "'Space Mono', monospace",
    },
}

PIXEL_ART = [
    "transparent","transparent","#2E4057","#2E4057","#E8622A","#E8622A","transparent","transparent",
    "transparent","#2E4057","#5DADE2","#0D0D0D","#0D0D0D","#F4D03F","#E8622A","transparent",
    "#2E4057","#0D0D0D","#0D0D0D","#5DADE2","#F4D03F","#0D0D0D","#E8622A","#E8622A",
    "#2E4057","#0D0D0D","#FFFFFF","#0D0D0D","#0D0D0D","#5DADE2","#F4D03F","#E8622A",
    "#E8622A","#0D0D0D","#0D0D0D","#FFFFFF","#5DADE2","#0D0D0D","#F4D03F","#2E4057",
    "#E8622A","#F4D03F","#0D0D0D","#0D0D0D","#0D0D0D","#FFFFFF","#2E4057","transparent",
    "transparent","#E8622A","#F4D03F","#5DADE2","#0D0D0D","#2E4057","transparent","transparent",
    "transparent","transparent","#E8622A","#E8622A","#2E4057","transparent","transparent","transparent",
]


def pick_theme(topic):
    tl = topic.lower()
    for name, t in THEMES.items():
        if name == "default":
            continue
        for kw in t["keywords"]:
            if re.search(r'\b' + re.escape(kw) + r'\b', tl):
                print(f"Theme: {name}  |  Layout: {t['layout']}  |  Matched: '{kw}'")
                return t
    print("Theme: default  |  Layout: tech")
    return THEMES["default"]


def load_style():
    with open(STYLE_CONFIG) as f:
        return json.load(f)


def image_to_base64(filepath):
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def fetch_unsplash_b64(query, width=1200, height=550):
    """Fetch a photo from Unsplash source and return as base64 data URI."""
    try:
        q = query.replace(" ", ",")
        url = f"https://source.unsplash.com/{width}x{height}/?{q}"
        r = requests.get(url, timeout=15, allow_redirects=True)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            b64 = base64.b64encode(r.content).decode("utf-8")
            ct  = r.headers.get("content-type", "image/jpeg").split(";")[0]
            print(f"  Fetched Unsplash image for '{query}' ({len(r.content)//1024}KB)")
            return f"data:{ct};base64,{b64}"
    except Exception as e:
        print(f"  Unsplash fetch failed: {e}")
    return None


def build_sources_html(citations, mono_font, accent):
    if not citations:
        return ""
    items = "".join(
        f'<li><a href="{c.get("url","#")}" target="_blank">[{c.get("index","")}] {c.get("title") or c.get("source_domain","")}</a></li>'
        for c in citations
    )
    return f"""
    <div style="margin-bottom:20px;">
      <p style="font-family:{mono_font};font-size:9px;text-transform:uppercase;letter-spacing:2px;color:{accent};margin-bottom:10px;">Sources</p>
      <ol style="padding-left:18px;font-family:{mono_font};font-size:10px;color:#666;line-height:1.7;">{items}</ol>
    </div>"""


def build_chart_images(images, accent, mono_font):
    if not images:
        return ""
    html = ""
    for img in images:
        b64 = img.get("base64_data_uri", "")
        if b64:
            html += f"""
  <div style="background:#FFFFFF;border-radius:12px;padding:16px;margin:16px 0;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
    <img src="{b64}" alt="{img.get('title','')}" style="width:100%;border-radius:8px;display:block;">
    <p style="font-family:{mono_font};font-size:11px;color:{accent};margin-top:10px;">▸ {img.get('title','')}</p>
  </div>"""
    return html


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: TRAVEL  — editorial magazine, full-bleed hero photo, serif typography
# ══════════════════════════════════════════════════════════════════════════════
def render_travel(content, theme, style, chart_images, citations, date_str):
    topic      = content.get("topic", "")
    headline   = content.get("headline", "")
    subhead    = content.get("subheadline", "")
    summary    = content.get("summary", "")
    sections   = content.get("sections", [])
    key_stats  = content.get("key_stats", [])
    citation_map = {c["index"]: c for c in citations}

    accent     = theme["accent"]
    accent2    = theme["accent2"]
    hf         = theme["heading_font"]
    bf         = theme["body_font"]
    mf         = theme["mono_font"]
    nl         = style.get("newsletter_name", "Newsletter")
    tagline    = style.get("footer_tagline", "")
    sender     = style.get("sender_name", "")

    # Fetch 3 Unsplash photos
    print("Fetching travel photos from Unsplash...")
    hero_img   = fetch_unsplash_b64(f"{topic},landscape,scenic", 1200, 600)
    mid_img    = fetch_unsplash_b64(f"{topic},travel,nature", 800, 450)
    footer_img = fetch_unsplash_b64(f"{topic},destination,beauty", 800, 350)

    hero_style = (
        f'background:linear-gradient(135deg,{accent}CC,{accent2}99);'
        if not hero_img else
        f'background:url("{hero_img}") center/cover no-repeat;'
    )

    # Stats as elegant horizontal pills
    stat_pills = ""
    for s in key_stats[:4]:
        stat_pills += f"""
        <div style="text-align:center;padding:16px 20px;">
          <div style="font-family:{mf};font-size:30px;font-weight:700;color:{accent};">{s.get('value','—')}</div>
          <div style="font-family:{bf};font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">{s.get('label','')}</div>
        </div>"""

    # Sections with pull-quote style alternating layout
    sect_html = ""
    pull_quotes = [s.get("body","").split(".")[0] + "." for s in sections]
    for i, s in enumerate(sections):
        paras = "".join(f'<p style="margin:0 0 16px;line-height:1.9;">{p.strip()}</p>' for p in s.get("body","").split("\n\n") if p.strip())
        pills = "".join(
            f'<a href="{citation_map[idx]["url"]}" style="display:inline-block;background:#F5F0EB;border-radius:20px;padding:2px 10px;font-family:{mf};font-size:10px;color:#999;margin:2px 4px 2px 0;text-decoration:none;" target="_blank">[{idx}] {citation_map[idx].get("source_domain","")}</a>'
            for idx in s.get("citation_indexes",[]) if idx in citation_map
        )

        # Insert mid photo after section 1
        photo_insert = ""
        if i == 1 and mid_img:
            photo_insert = f'<div style="margin:32px 0;border-radius:12px;overflow:hidden;"><img src="{mid_img}" style="width:100%;display:block;" alt="{topic}"></div>'

        # Alternate pull-quote side
        pq = pull_quotes[i] if i < len(pull_quotes) else ""
        if i % 2 == 0:
            sect_html += f"""
  {photo_insert}
  <div style="background:#FFFFFF;border-radius:16px;padding:36px 40px;margin:16px 0;box-shadow:0 2px 20px rgba(0,0,0,0.05);">
    <div style="display:flex;gap:32px;align-items:flex-start;">
      <div style="flex:1;">
        <p style="font-family:{mf};font-size:11px;color:{accent};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">0{i+1}</p>
        <h2 style="font-family:{hf};font-size:26px;font-weight:700;color:#1a1a1a;margin:0 0 18px;line-height:1.25;">{s.get('heading','')}</h2>
        <div style="font-family:{bf};font-size:15px;color:#555;">{paras}</div>
        {f'<div style="margin-top:16px;">{pills}</div>' if pills else ''}
      </div>
      <div style="width:180px;flex-shrink:0;border-left:3px solid {accent};padding-left:20px;padding-top:8px;">
        <p style="font-family:{hf};font-style:italic;font-size:17px;color:#333;line-height:1.6;">"{pq}"</p>
      </div>
    </div>
  </div>"""
        else:
            sect_html += f"""
  {photo_insert}
  <div style="background:#FFFFFF;border-radius:16px;padding:36px 40px;margin:16px 0;box-shadow:0 2px 20px rgba(0,0,0,0.05);">
    <div style="display:flex;gap:32px;align-items:flex-start;">
      <div style="width:180px;flex-shrink:0;border-right:3px solid {accent2};padding-right:20px;padding-top:8px;">
        <p style="font-family:{hf};font-style:italic;font-size:17px;color:#333;line-height:1.6;">"{pq}"</p>
      </div>
      <div style="flex:1;">
        <p style="font-family:{mf};font-size:11px;color:{accent2};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">0{i+1}</p>
        <h2 style="font-family:{hf};font-size:26px;font-weight:700;color:#1a1a1a;margin:0 0 18px;line-height:1.25;">{s.get('heading','')}</h2>
        <div style="font-family:{bf};font-size:15px;color:#555;">{paras}</div>
        {f'<div style="margin-top:16px;">{pills}</div>' if pills else ''}
      </div>
    </div>
  </div>"""

    footer_photo = f'<img src="{footer_img}" style="width:100%;height:200px;object-fit:cover;display:block;border-radius:12px;margin-bottom:28px;" alt="{topic}">' if footer_img else ""
    charts = build_chart_images(chart_images, accent, mf)
    sources = build_sources_html(citations, mf, accent)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{nl}: {topic}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{theme['fonts']}" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:{theme['page_bg']};font-family:{bf};-webkit-font-smoothing:antialiased;padding:0 0 60px;}}
    @keyframes fadeIn{{from{{opacity:0;transform:translateY(20px);}}to{{opacity:1;transform:translateY(0);}}}}
    .fade{{animation:fadeIn .7s ease both;}}
    a{{color:inherit;}}
  </style>
</head>
<body>
  <div style="max-width:740px;margin:0 auto;padding:32px 16px 0;">

    <!-- MASTHEAD -->
    <div class="fade" style="text-align:center;padding:28px 0 20px;border-bottom:1px solid #DDD;margin-bottom:0;">
      <p style="font-family:{mf};font-size:10px;letter-spacing:4px;text-transform:uppercase;color:#999;">{date_str}</p>
      <h1 style="font-family:{hf};font-size:38px;font-weight:900;color:#1a1a1a;letter-spacing:-1px;margin:8px 0 6px;">{nl}</h1>
      <p style="font-family:{bf};font-size:13px;color:#999;letter-spacing:1px;">{tagline.upper()}</p>
    </div>

    <!-- FULL-BLEED HERO IMAGE -->
    <div class="fade" style="margin:0;position:relative;border-radius:0;overflow:hidden;height:500px;{hero_style}">
      <div style="position:absolute;inset:0;background:{theme['hero_overlay']};"></div>
      <div style="position:absolute;bottom:0;left:0;right:0;padding:48px 52px;">
        <p style="font-family:{mf};font-size:11px;letter-spacing:3px;text-transform:uppercase;color:{accent2};margin-bottom:14px;">Cover Story</p>
        <h2 style="font-family:{hf};font-size:clamp(34px,6vw,54px);font-weight:900;color:#FFFFFF;line-height:1.05;letter-spacing:-1px;max-width:560px;">{headline}</h2>
        <p style="font-family:{bf};font-size:16px;color:rgba(255,255,255,0.8);margin-top:16px;max-width:480px;line-height:1.6;">{subhead}</p>
      </div>
    </div>

    <!-- STATS BAR -->
    <div class="fade" style="background:#1a1a1a;display:flex;justify-content:center;flex-wrap:wrap;gap:0;border-bottom:3px solid {accent};">
      {stat_pills}
    </div>

    <!-- SUMMARY / INTRO -->
    <div class="fade" style="background:#FFFFFF;padding:40px 48px;margin:16px 0;border-radius:16px;box-shadow:0 2px 20px rgba(0,0,0,0.05);position:relative;overflow:hidden;">
      <div style="position:absolute;top:-20px;left:32px;font-family:{hf};font-size:160px;color:{accent};opacity:0.06;font-weight:900;line-height:1;">"</div>
      <p style="font-family:{mf};font-size:10px;letter-spacing:3px;text-transform:uppercase;color:{accent};margin-bottom:16px;">Editor's Note</p>
      <p style="font-family:{hf};font-size:20px;font-weight:400;font-style:italic;color:#1a1a1a;line-height:1.75;position:relative;z-index:1;">{summary}</p>
    </div>

    <!-- SECTIONS -->
    {sect_html}

    <!-- CHARTS -->
    {charts}

    <!-- FOOTER PHOTO + FOOTER -->
    <div class="fade" style="margin-top:24px;">
      {footer_photo}
      <div style="background:{theme['footer_bg']};border-radius:16px;padding:36px 40px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px;gap:16px;">
          <div>
            <p style="font-family:{hf};font-size:22px;font-weight:700;color:#FFFFFF;">{nl}</p>
            <p style="font-family:{bf};font-size:12px;color:#888;margin-top:4px;">{tagline}</p>
          </div>
          <div style="background:{accent};color:#fff;font-family:{mf};font-size:9px;padding:8px 16px;border-radius:6px;letter-spacing:1px;text-transform:uppercase;white-space:nowrap;">{date_str}</div>
        </div>
        {sources}
        <hr style="border:none;border-top:1px solid #2a2a2a;margin:20px 0;">
        <p style="font-family:{bf};font-size:11px;color:#444;line-height:1.7;">Generated {date_str} · {sender}<br>You're receiving this newsletter. <a href="#" style="color:#666;">Unsubscribe</a>.</p>
      </div>
    </div>

  </div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: FINANCE  — Bloomberg/WSJ style, data-first, serif editorial
# ══════════════════════════════════════════════════════════════════════════════
def render_finance(content, theme, style, chart_images, citations, date_str):
    topic      = content.get("topic","")
    headline   = content.get("headline","")
    subhead    = content.get("subheadline","")
    summary    = content.get("summary","")
    sections   = content.get("sections",[])
    key_stats  = content.get("key_stats",[])
    citation_map = {c["index"]: c for c in citations}

    accent  = theme["accent"]
    accent2 = theme["accent2"]
    hf = theme["heading_font"]
    bf = theme["body_font"]
    mf = theme["mono_font"]
    nl = style.get("newsletter_name","Newsletter")
    tagline = style.get("footer_tagline","")
    sender  = style.get("sender_name","")

    stat_cards = ""
    arrows = ["▲", "▼", "▲", "▼"]
    acolors = ["#27AE60","#E74C3C","#27AE60","#E74C3C"]
    for i, s in enumerate(key_stats[:4]):
        stat_cards += f"""
      <div style="flex:1;border-top:3px solid {'#B8860B' if i%2==0 else '#2471A3'};padding:18px 16px;background:#FDFCF8;">
        <div style="font-family:{mf};font-size:9px;color:#999;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">{s.get('label','')}</div>
        <div style="font-family:{mf};font-size:32px;font-weight:600;color:#1a1a1a;line-height:1;">{s.get('value','—')}</div>
        <div style="font-family:{mf};font-size:11px;color:{acolors[i%4]};margin-top:6px;">{arrows[i%4]} vs prior period</div>
      </div>"""

    sects = ""
    for i, s in enumerate(sections):
        paras = "".join(f'<p style="margin:0 0 14px;line-height:1.85;">{p.strip()}</p>' for p in s.get("body","").split("\n\n") if p.strip())
        pills = "".join(
            f'<a href="{citation_map[idx]["url"]}" style="font-family:{mf};font-size:9px;color:#999;margin-right:10px;text-decoration:none;" target="_blank">[{idx}]</a>'
            for idx in s.get("citation_indexes",[]) if idx in citation_map
        )
        sects += f"""
  <div style="padding:28px 0;border-bottom:1px solid #E8E4DC;">
    <div style="display:flex;gap:24px;">
      <div style="width:48px;flex-shrink:0;text-align:right;">
        <span style="font-family:{mf};font-size:36px;font-weight:600;color:#DDD;line-height:1;">{str(i+1).zfill(2)}</span>
      </div>
      <div style="flex:1;">
        <h2 style="font-family:{hf};font-size:22px;font-weight:700;color:#1a1a1a;margin-bottom:14px;line-height:1.3;">{s.get('heading','')}</h2>
        <div style="font-family:{bf};font-size:14.5px;color:#444;">{paras}</div>
        {f'<div style="margin-top:12px;">{pills}</div>' if pills else ''}
      </div>
    </div>
  </div>"""

    charts = build_chart_images(chart_images, accent, mf)
    sources = build_sources_html(citations, mf, accent)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{nl}: {topic}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{theme['fonts']}" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:{theme['page_bg']};font-family:{bf};-webkit-font-smoothing:antialiased;padding:0 0 60px;}}
    @keyframes fadeIn{{from{{opacity:0;transform:translateY(16px);}}to{{opacity:1;transform:translateY(0);}}}}
    .fade{{animation:fadeIn .6s ease both;}}
  </style>
</head>
<body>
  <div style="max-width:740px;margin:0 auto;padding:32px 16px 0;">

    <!-- HEADER BAR -->
    <div class="fade" style="border-top:4px solid {accent};border-bottom:1px solid #222;padding:14px 0;display:flex;justify-content:space-between;align-items:center;margin-bottom:28px;">
      <h1 style="font-family:{hf};font-size:28px;font-weight:700;color:#1a1a1a;letter-spacing:-0.5px;">{nl}</h1>
      <div style="text-align:right;">
        <p style="font-family:{mf};font-size:9px;color:#999;letter-spacing:1px;">{date_str}</p>
        <p style="font-family:{mf};font-size:9px;color:{accent};letter-spacing:1px;margin-top:2px;">MARKETS &amp; ECONOMY</p>
      </div>
    </div>

    <!-- HEADLINE -->
    <div class="fade" style="margin-bottom:24px;">
      <h2 style="font-family:{hf};font-size:clamp(30px,5.5vw,48px);font-weight:700;color:#1a1a1a;line-height:1.1;letter-spacing:-1px;margin-bottom:14px;">{headline}</h2>
      <p style="font-family:{bf};font-size:17px;color:#555;line-height:1.6;border-left:3px solid {accent};padding-left:16px;">{subhead}</p>
    </div>

    <!-- STATS ROW -->
    <div class="fade" style="display:flex;gap:0;border:1px solid #E8E4DC;border-radius:8px;overflow:hidden;margin-bottom:24px;">
      {stat_cards}
    </div>

    <!-- SUMMARY -->
    <div class="fade" style="background:#0A1628;padding:28px 32px;border-radius:8px;margin-bottom:24px;">
      <p style="font-family:{mf};font-size:9px;color:{accent};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">Executive Summary</p>
      <p style="font-family:{hf};font-size:17px;color:#FFFFFF;line-height:1.8;font-style:italic;">{summary}</p>
    </div>

    <!-- SECTIONS -->
    <div class="fade">
      {sects}
    </div>

    <!-- CHARTS -->
    {charts}

    <!-- FOOTER -->
    <div class="fade" style="background:{theme['footer_bg']};border-radius:8px;padding:32px 36px;margin-top:28px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:22px;">
        <p style="font-family:{hf};font-size:20px;font-weight:700;color:#FFF;">{nl}</p>
        <p style="font-family:{mf};font-size:9px;color:{accent};letter-spacing:1px;align-self:center;">{tagline.upper()}</p>
      </div>
      {sources}
      <hr style="border:none;border-top:1px solid #1e2a3a;margin:18px 0;">
      <p style="font-family:{bf};font-size:11px;color:#3a3a3a;line-height:1.7;">Generated {date_str} · {sender}<br><a href="#" style="color:#555;">Unsubscribe</a></p>
    </div>

  </div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: HEALTH  — clean clinical report, Inter font, card grid
# ══════════════════════════════════════════════════════════════════════════════
def render_health(content, theme, style, chart_images, citations, date_str):
    topic      = content.get("topic","")
    headline   = content.get("headline","")
    subhead    = content.get("subheadline","")
    summary    = content.get("summary","")
    sections   = content.get("sections",[])
    key_stats  = content.get("key_stats",[])
    citation_map = {c["index"]: c for c in citations}

    accent  = theme["accent"]
    accent2 = theme["accent2"]
    hf = theme["heading_font"]
    bf = theme["body_font"]
    mf = theme["mono_font"]
    nl = style.get("newsletter_name","Newsletter")
    tagline = style.get("footer_tagline","")
    sender  = style.get("sender_name","")

    stat_grid = ""
    colors = [accent, "#6C3483", accent2, "#17A589"]
    for i, s in enumerate(key_stats[:4]):
        c = colors[i % len(colors)]
        stat_grid += f"""
      <div style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.06);">
        <div style="height:4px;background:{c};"></div>
        <div style="padding:20px 22px;">
          <div style="font-family:{mf};font-size:36px;font-weight:700;color:{c};line-height:1;">{s.get('value','—')}</div>
          <div style="font-family:{bf};font-size:11px;color:#888;margin-top:6px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">{s.get('label','')}</div>
        </div>
      </div>"""

    sects = ""
    for i, s in enumerate(sections):
        c = colors[i % len(colors)]
        paras = "".join(f'<p style="margin:0 0 14px;line-height:1.85;">{p.strip()}</p>' for p in s.get("body","").split("\n\n") if p.strip())
        pills = "".join(
            f'<a href="{citation_map[idx]["url"]}" style="display:inline-block;background:#EFF6FB;border-radius:4px;padding:2px 8px;font-family:{mf};font-size:9px;color:{accent};margin:2px 4px 2px 0;text-decoration:none;" target="_blank">[{idx}]</a>'
            for idx in s.get("citation_indexes",[]) if idx in citation_map
        )
        sects += f"""
  <div style="background:#FFFFFF;border-radius:14px;padding:28px 32px;margin:10px 0;box-shadow:0 2px 12px rgba(0,0,0,0.05);display:flex;gap:0;overflow:hidden;">
    <div style="width:5px;background:{c};flex-shrink:0;border-radius:3px;margin-right:26px;"></div>
    <div style="flex:1;">
      <div style="display:inline-block;background:{c}18;color:{c};font-family:{mf};font-size:9px;letter-spacing:2px;padding:3px 10px;border-radius:4px;text-transform:uppercase;margin-bottom:12px;font-weight:600;">Finding 0{i+1}</div>
      <h2 style="font-family:{hf};font-size:20px;font-weight:700;color:#0D2137;margin-bottom:12px;line-height:1.3;">{s.get('heading','')}</h2>
      <div style="font-family:{bf};font-size:14.5px;color:#444;">{paras}</div>
      {f'<div style="margin-top:14px;">{pills}</div>' if pills else ''}
    </div>
  </div>"""

    charts = build_chart_images(chart_images, accent, mf)
    sources = build_sources_html(citations, mf, accent)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{nl}: {topic}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{theme['fonts']}" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:{theme['page_bg']};font-family:{bf};-webkit-font-smoothing:antialiased;padding:40px 16px 60px;}}
    @keyframes fadeIn{{from{{opacity:0;transform:translateY(16px);}}to{{opacity:1;transform:translateY(0);}}}}
    .fade{{animation:fadeIn .6s ease both;}}
  </style>
</head>
<body>
  <div style="max-width:740px;margin:0 auto;">

    <!-- HEADER -->
    <div class="fade" style="background:#FFFFFF;border-radius:16px 16px 0 0;padding:28px 36px;border-bottom:1px solid #E8F0FA;display:flex;align-items:center;justify-content:space-between;">
      <div>
        <p style="font-family:{mf};font-size:9px;color:{accent};letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">{nl}</p>
        <h1 style="font-family:{hf};font-size:clamp(26px,5vw,42px);font-weight:800;color:#0D2137;line-height:1.1;letter-spacing:-1px;">{headline}</h1>
        <p style="font-family:{bf};font-size:15px;color:#5A7A9A;margin-top:10px;line-height:1.55;">{subhead}</p>
      </div>
      <div style="flex-shrink:0;margin-left:24px;">
        <div style="width:80px;height:80px;border-radius:50%;border:3px solid {accent};display:flex;align-items:center;justify-content:center;text-align:center;">
          <div>
            <div style="font-family:{mf};font-size:9px;color:{accent};text-transform:uppercase;">Issue</div>
            <div style="font-family:{hf};font-size:13px;font-weight:700;color:#0D2137;margin-top:2px;">{date_str.split(' ')[1]}<br>{date_str.split(' ')[0][:3]}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- STAT GRID -->
    <div class="fade" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0;">
      {stat_grid}
    </div>

    <!-- SUMMARY -->
    <div class="fade" style="background:linear-gradient(135deg,{accent},{accent2});border-radius:14px;padding:28px 32px;margin:10px 0;">
      <p style="font-family:{mf};font-size:9px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">Summary</p>
      <p style="font-family:{bf};font-size:15.5px;color:#FFFFFF;line-height:1.8;font-weight:400;">{summary}</p>
    </div>

    <!-- SECTIONS -->
    {sects}

    <!-- CHARTS -->
    {charts}

    <!-- FOOTER -->
    <div class="fade" style="background:{theme['footer_bg']};border-radius:0 0 16px 16px;padding:32px 36px;margin-top:10px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:20px;">
        <p style="font-family:{hf};font-size:18px;font-weight:700;color:#FFF;">{nl}</p>
        <span style="background:{accent};color:#fff;font-family:{mf};font-size:9px;padding:5px 12px;border-radius:4px;letter-spacing:1px;text-transform:uppercase;align-self:center;">{date_str}</span>
      </div>
      {sources}
      <hr style="border:none;border-top:1px solid #1a2a3a;margin:16px 0;">
      <p style="font-family:{bf};font-size:11px;color:#3a3a3a;line-height:1.7;">Generated {date_str} · {sender}<br><a href="#" style="color:#555;">Unsubscribe</a></p>
    </div>

  </div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: ECO  — DM Sans, organic feel, badge-style stats
# ══════════════════════════════════════════════════════════════════════════════
def render_eco(content, theme, style, chart_images, citations, date_str):
    topic      = content.get("topic","")
    headline   = content.get("headline","")
    subhead    = content.get("subheadline","")
    summary    = content.get("summary","")
    sections   = content.get("sections",[])
    key_stats  = content.get("key_stats",[])
    citation_map = {c["index"]: c for c in citations}

    accent  = theme["accent"]
    accent2 = theme["accent2"]
    hf = theme["heading_font"]
    bf = theme["body_font"]
    mf = theme["mono_font"]
    nl = style.get("newsletter_name","Newsletter")
    tagline = style.get("footer_tagline","")
    sender  = style.get("sender_name","")

    icons = ["🌱","⚡","🔋","🌍"]
    stat_row = ""
    for i, s in enumerate(key_stats[:4]):
        stat_row += f"""
      <div style="flex:1;background:#FFFFFF;border-radius:14px;padding:20px 14px;text-align:center;border:2px solid {accent if i%2==0 else accent2}22;box-shadow:0 2px 10px rgba(0,0,0,0.04);">
        <div style="font-size:24px;margin-bottom:8px;">{icons[i%4]}</div>
        <div style="font-family:{mf};font-size:30px;font-weight:700;color:{accent if i%2==0 else accent2};line-height:1;">{s.get('value','—')}</div>
        <div style="font-family:{bf};font-size:11px;color:#777;margin-top:6px;font-weight:600;">{s.get('label','')}</div>
      </div>"""

    sects = ""
    eco_icons = ["🌿","☀️","💧","🏔️"]
    for i, s in enumerate(sections):
        paras = "".join(f'<p style="margin:0 0 14px;line-height:1.85;">{p.strip()}</p>' for p in s.get("body","").split("\n\n") if p.strip())
        pills = "".join(
            f'<a href="{citation_map[idx]["url"]}" style="display:inline-block;background:#E9F7EF;border-radius:20px;padding:2px 10px;font-family:{mf};font-size:9px;color:{accent};margin:2px 4px 2px 0;text-decoration:none;" target="_blank">[{idx}] {citation_map[idx].get("source_domain","")}</a>'
            for idx in s.get("citation_indexes",[]) if idx in citation_map
        )
        acc = accent if i % 2 == 0 else accent2
        sects += f"""
  <div style="background:#FFFFFF;border-radius:16px;margin:10px 0;box-shadow:0 2px 12px rgba(0,0,0,0.05);overflow:hidden;border-top:4px solid {acc};">
    <div style="background:{acc}0D;padding:16px 28px 12px;display:flex;align-items:center;gap:12px;">
      <span style="font-size:22px;">{eco_icons[i%4]}</span>
      <h2 style="font-family:{hf};font-size:20px;font-weight:700;color:{acc};">{s.get('heading','')}</h2>
    </div>
    <div style="padding:18px 28px 24px;">
      <div style="font-family:{bf};font-size:14.5px;color:#444;">{paras}</div>
      {f'<div style="margin-top:14px;">{pills}</div>' if pills else ''}
    </div>
  </div>"""

    charts = build_chart_images(chart_images, accent, mf)
    sources = build_sources_html(citations, mf, accent)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{nl}: {topic}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{theme['fonts']}" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:{theme['page_bg']};font-family:{bf};-webkit-font-smoothing:antialiased;padding:40px 16px 60px;}}
    @keyframes fadeIn{{from{{opacity:0;transform:translateY(16px);}}to{{opacity:1;transform:translateY(0);}}}}
    .fade{{animation:fadeIn .6s ease both;}}
  </style>
</head>
<body>
  <div style="max-width:740px;margin:0 auto;">

    <!-- HERO -->
    <div class="fade" style="background:linear-gradient(135deg,{theme['footer_bg']},{accent}CC);border-radius:20px;padding:52px 48px;margin-bottom:12px;position:relative;overflow:hidden;">
      <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,0.04);"></div>
      <div style="position:absolute;bottom:-60px;left:-20px;width:160px;height:160px;border-radius:50%;background:{accent2}22;"></div>
      <div style="position:relative;z-index:1;">
        <div style="display:inline-block;background:{accent}33;border:1px solid {accent}66;border-radius:20px;padding:4px 14px;font-family:{mf};font-size:9px;color:{accent};letter-spacing:2px;text-transform:uppercase;margin-bottom:18px;">{nl} &nbsp;·&nbsp; Weekly</div>
        <h1 style="font-family:{hf};font-size:clamp(36px,7vw,60px);font-weight:700;color:#FFFFFF;line-height:0.95;letter-spacing:-2px;margin-bottom:18px;">{headline}</h1>
        <p style="font-family:{bf};font-size:16px;color:rgba(255,255,255,0.75);line-height:1.6;max-width:440px;">{subhead}</p>
        <p style="font-family:{mf};font-size:10px;color:{accent};margin-top:22px;letter-spacing:1px;">// {date_str}</p>
      </div>
    </div>

    <!-- STAT ROW -->
    <div class="fade" style="display:flex;gap:10px;margin-bottom:12px;">{stat_row}</div>

    <!-- SUMMARY -->
    <div class="fade" style="background:#FFFFFF;border-radius:16px;padding:28px 32px;margin-bottom:12px;border-left:5px solid {accent};box-shadow:0 2px 12px rgba(0,0,0,0.05);">
      <p style="font-family:{mf};font-size:9px;color:{accent};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">TL;DR</p>
      <p style="font-family:{bf};font-size:15.5px;color:#222;line-height:1.8;font-weight:500;">{summary}</p>
    </div>

    <!-- SECTIONS -->
    {sects}

    <!-- CHARTS -->
    {charts}

    <!-- FOOTER -->
    <div class="fade" style="background:{theme['footer_bg']};border-radius:16px;padding:32px 36px;margin-top:12px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:20px;align-items:flex-start;">
        <div>
          <p style="font-family:{hf};font-size:18px;font-weight:700;color:#FFF;">{nl}</p>
          <p style="font-family:{bf};font-size:12px;color:#888;margin-top:4px;">{tagline}</p>
        </div>
        <span style="background:{accent};color:#fff;font-family:{mf};font-size:9px;padding:5px 12px;border-radius:20px;letter-spacing:1px;text-transform:uppercase;">{date_str}</span>
      </div>
      {sources}
      <hr style="border:none;border-top:1px solid #1a2a1a;margin:16px 0;">
      <p style="font-family:{bf};font-size:11px;color:#3a3a3a;line-height:1.7;">Generated {date_str} · {sender}<br><a href="#" style="color:#555;">Unsubscribe</a></p>
    </div>

  </div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: TECH  — Space Grotesk, dark hero, pixel art, ticker
# ══════════════════════════════════════════════════════════════════════════════
def render_tech(content, theme, style, chart_images, citations, date_str):
    topic      = content.get("topic","")
    headline   = content.get("headline","")
    subhead    = content.get("subheadline","")
    summary    = content.get("summary","")
    sections   = content.get("sections",[])
    key_stats  = content.get("key_stats",[])
    citation_map = {c["index"]: c for c in citations}

    accent  = theme["accent"]
    accent2 = theme["accent2"]
    hf = theme["heading_font"]
    bf = theme["body_font"]
    mf = theme["mono_font"]
    nl = style.get("newsletter_name","Newsletter")
    tagline = style.get("footer_tagline","")
    sender  = style.get("sender_name","")

    pixel_divs = "\n".join(
        f'<div style="width:20px;height:20px;border-radius:3px;background:{"transparent" if c=="transparent" else c};"></div>'
        for c in PIXEL_ART
    )

    stat_colors = [accent, "#2E4057", accent2, "#27AE60"]
    stat_text   = ["#FFF","#FFF","#0D0D0D","#FFF"]
    stat_row = ""
    for i, s in enumerate(key_stats[:4]):
        bg = stat_colors[i%4]; tx = stat_text[i%4]
        lc = "rgba(0,0,0,0.5)" if tx=="#0D0D0D" else "rgba(255,255,255,0.65)"
        stat_row += f'<div style="flex:1;background:{bg};border-radius:14px;padding:22px 14px 18px;text-align:center;"><div style="font-family:{mf};font-size:38px;font-weight:700;color:{tx};line-height:1;">{s.get("value","—")}</div><div style="font-family:{bf};font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:{lc};margin-top:6px;">{s.get("label","")}</div></div>'

    ticker_items = " &nbsp;·&nbsp; ".join(f"{s.get('value','')} {s.get('label','')}" for s in key_stats)
    ticker = f"<span>{ticker_items}</span><span style='color:#444;'>&nbsp;&nbsp;///&nbsp;&nbsp;</span><span>{ticker_items}</span><span style='color:#444;'>&nbsp;&nbsp;///&nbsp;&nbsp;</span>"

    sects = ""
    sec_colors = [accent,"#2E4057","#27AE60","#8E44AD"]
    for i, s in enumerate(sections):
        acc = sec_colors[i%4]
        paras = "".join(f'<p style="margin:0 0 12px;line-height:1.85;">{p.strip()}</p>' for p in s.get("body","").split("\n\n") if p.strip())
        pills = "".join(
            f'<a href="{citation_map[idx]["url"]}" style="display:inline-block;background:#F0EDE8;border-radius:20px;padding:2px 10px;font-family:{mf};font-size:9px;color:#888;margin:2px 4px 2px 0;text-decoration:none;" target="_blank">[{idx}] {citation_map[idx].get("source_domain","")}</a>'
            for idx in s.get("citation_indexes",[]) if idx in citation_map
        )
        sects += f'<div style="display:flex;background:#FFFFFF;border-radius:14px;overflow:hidden;margin:10px 0;box-shadow:0 2px 14px rgba(0,0,0,0.05);"><div style="width:5px;background:{acc};flex-shrink:0;"></div><div style="padding:24px 28px;flex:1;"><h2 style="font-family:{hf};font-size:20px;font-weight:800;color:{acc};margin-bottom:12px;">{s.get("heading","")}</h2><div style="font-family:{bf};font-size:14.5px;color:#444;">{paras}</div>{f"<div style=margin-top:14px;>{pills}</div>" if pills else ""}</div></div>'

    prog_rows = ""
    for i, s in enumerate(key_stats[:4]):
        raw = s.get("value","0").replace("%","").replace("+","").replace("x","").split("-")[0]
        try: pct = min(float(raw), 100)
        except: pct = 60
        c = stat_colors[i%4]
        prog_rows += f'<div style="margin-bottom:13px;"><div style="display:flex;justify-content:space-between;font-size:12px;font-weight:700;color:#333;margin-bottom:5px;font-family:{bf};"><span>{s.get("label","")}</span><span>{s.get("value","")}</span></div><div style="height:7px;background:#EEEAE4;border-radius:4px;overflow:hidden;"><div style="width:{pct}%;height:100%;background:{c};border-radius:4px;"></div></div></div>'

    charts = build_chart_images(chart_images, accent, mf)
    sources = build_sources_html(citations, mf, accent)

    words = headline.split()
    hero_title = " ".join(words[:-1]) + f' <em style="color:{accent};font-style:normal;">{words[-1]}</em>' if len(words)>1 else headline

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{nl}: {topic}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{theme['fonts']}" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:{theme['page_bg']};font-family:{bf};-webkit-font-smoothing:antialiased;padding:40px 16px 60px;}}
    @keyframes fadeIn{{from{{opacity:0;transform:translateY(20px);}}to{{opacity:1;transform:translateY(0);}}}}
    @keyframes ticker{{0%{{transform:translateX(0);}}100%{{transform:translateX(-50%);}}}}
    @keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.4;}}}}
    .fade{{animation:fadeIn .55s cubic-bezier(.22,1,.36,1) both;}}
  </style>
</head>
<body>
  <div style="max-width:740px;margin:0 auto;">

    <!-- TICKER -->
    <div class="fade" style="background:{theme['footer_bg']};overflow:hidden;padding:10px 0;border-radius:12px 12px 0 0;">
      <div style="display:flex;white-space:nowrap;animation:ticker 20s linear infinite;">
        <span style="font-family:{mf};font-size:11px;color:{accent};padding:0 24px;letter-spacing:1px;">{ticker}</span>
      </div>
    </div>

    <!-- HERO -->
    <div class="fade" style="background:{theme['footer_bg']};padding:52px 52px 56px;display:flex;align-items:center;justify-content:space-between;gap:32px;position:relative;overflow:hidden;">
      <div style="position:absolute;inset:0;background:radial-gradient(ellipse at 70% 50%,{accent}2E 0%,transparent 65%);pointer-events:none;"></div>
      <div style="flex:1;min-width:0;position:relative;z-index:1;">
        <div style="display:inline-flex;align-items:center;gap:8px;background:{accent}22;border:1px solid {accent}55;border-radius:20px;padding:4px 14px;font-family:{mf};font-size:10px;color:{accent};letter-spacing:2px;text-transform:uppercase;margin-bottom:18px;">
          <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:{accent};animation:pulse 2s ease infinite;"></span>{nl}
        </div>
        <h1 style="font-family:{hf};font-size:clamp(44px,8vw,72px);font-weight:800;line-height:0.93;color:#FFFFFF;letter-spacing:-3px;">{hero_title}</h1>
        <p style="font-family:{bf};font-size:16px;color:#888;line-height:1.6;margin-top:18px;max-width:400px;">{subhead}</p>
        <div style="display:flex;gap:16px;margin-top:22px;align-items:center;">
          <span style="font-family:{mf};font-size:10px;color:#555;letter-spacing:1px;">// {date_str}</span>
          <span style="background:{accent};color:#fff;font-family:{mf};font-size:9px;padding:3px 10px;border-radius:4px;text-transform:uppercase;letter-spacing:1px;">WEEKLY BRIEF</span>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(8,20px);grid-template-rows:repeat(8,20px);gap:3px;flex-shrink:0;z-index:1;">{pixel_divs}</div>
    </div>

    <!-- SUMMARY -->
    <div class="fade" style="background:#FFFFFF;padding:28px 36px;border-left:5px solid {accent};position:relative;overflow:hidden;">
      <div style="position:absolute;top:-10px;right:28px;font-size:120px;font-weight:800;color:{accent};opacity:0.06;line-height:1;font-family:{hf};">"</div>
      <p style="font-family:{mf};font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:3px;color:{accent};margin-bottom:10px;">TL;DR</p>
      <p style="font-family:{bf};font-size:16px;font-weight:500;color:#1a1a1a;line-height:1.8;position:relative;z-index:1;">{summary}</p>
    </div>

    <!-- STATS -->
    <div class="fade" style="display:flex;gap:8px;padding-top:12px;">{stat_row}</div>

    <!-- PROGRESS -->
    <div class="fade" style="background:#FFFFFF;border-radius:14px;padding:26px 30px;margin-top:10px;box-shadow:0 2px 14px rgba(0,0,0,0.05);">
      <p style="font-family:{mf};font-size:9px;text-transform:uppercase;letter-spacing:2px;color:{accent};margin-bottom:14px;">Key Metrics</p>
      {prog_rows}
    </div>

    <!-- SECTIONS -->
    {sects}

    <!-- CHARTS -->
    {charts}

    <!-- FOOTER -->
    <div style="height:6px;background:{theme.get('gradient_bar', f'linear-gradient(90deg,{accent},{accent2})')};" class="fade"></div>
    <footer class="fade" style="background:{theme['footer_bg']};border-radius:0 0 16px 16px;padding:32px 36px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:22px;gap:16px;">
        <div><p style="font-family:{hf};font-size:18px;font-weight:800;color:#FFF;">{nl}</p><p style="font-family:{bf};font-size:12px;color:#888;margin-top:4px;">{tagline}</p></div>
        <span style="background:{accent};color:#fff;font-family:{mf};font-size:9px;padding:6px 14px;border-radius:6px;letter-spacing:1px;text-transform:uppercase;white-space:nowrap;">{date_str}</span>
      </div>
      {sources}
      <hr style="border:none;border-top:1px solid #1e1e1e;margin:18px 0;">
      <p style="font-family:{bf};font-size:11px;color:#3a3a3a;line-height:1.7;">Generated {date_str} · {sender}<br><a href="#" style="color:#555;">Unsubscribe</a></p>
    </footer>

  </div>
</body>
</html>"""


# ── MAIN ───────────────────────────────────────────────────────────────────────
def render_html():
    if not os.path.exists(CONTENT_PATH):
        sys.exit(f"Error: {CONTENT_PATH} not found. Run synthesize.py first.")

    style = load_style()
    with open(CONTENT_PATH) as f:
        content = json.load(f)

    topic = content.get("topic", "")
    theme = pick_theme(topic)
    layout = theme["layout"]

    infographics = []
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH) as f:
            infographics = json.load(f).get("infographics", [])

    chart_images = []
    for item in infographics:
        fp = item.get("filepath", "")
        if os.path.exists(fp):
            b64 = image_to_base64(fp)
            chart_images.append({"title": item["title"], "base64_data_uri": f"data:image/png;base64,{b64}"})

    citations = content.get("citations", [])
    date_str  = datetime.utcnow().strftime("%B %d, %Y").upper()

    dispatch = {
        "travel":  render_travel,
        "eco":     render_eco,
        "finance": render_finance,
        "health":  render_health,
        "tech":    render_tech,
    }
    renderer = dispatch.get(layout, render_tech)
    html = renderer(content, theme, style, chart_images, citations, date_str)

    os.makedirs(".tmp", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(html)

    size_kb = len(html.encode("utf-8")) / 1024
    print(f"HTML render complete: {size_kb:.1f} KB  |  layout: {layout}")
    print(f"Output: {OUTPUT_PATH}")
    return html


if __name__ == "__main__":
    render_html()
