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

CONTENT_PATH  = ".tmp/newsletter_content.json"
MANIFEST_PATH = ".tmp/infographics/manifest.json"
OUTPUT_PATH   = ".tmp/newsletter_final.html"
STYLE_CONFIG  = "config/newsletter_style.json"
LOGO_PATH     = "brand_assets/Bold Industrial Logo Design for MR.png"


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
        "accent": "#F5B201",
        "accent2": "#F07A14",
        "page_bg": "#0C1220",
        "footer_bg": "#0C1220",
        "fonts": "https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Exo+2:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700;800;900&family=Roboto+Mono:wght@400;500&display=swap",
        "heading_font": "'Oswald', sans-serif",
        "body_font": "'Exo 2', sans-serif",
        "mono_font": "'Roboto Mono', monospace",
    },
    "default": {
        "keywords": [],
        "layout": "tech",
        "accent": "#F5B201",
        "accent2": "#F07A14",
        "page_bg": "#0C1220",
        "footer_bg": "#0C1220",
        "fonts": "https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Exo+2:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700;800;900&family=Roboto+Mono:wght@400;500&display=swap",
        "heading_font": "'Oswald', sans-serif",
        "body_font": "'Exo 2', sans-serif",
        "mono_font": "'Roboto Mono', monospace",
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


def load_brand_logo_b64(max_px=128):
    """
    Return the MR Industries logo as a base64 data URI, resized to max_px.
    Falls back to raw file if Pillow is unavailable.
    """
    if not os.path.exists(LOGO_PATH):
        return None
    try:
        from PIL import Image
        import io as _io
        img = Image.open(LOGO_PATH).convert("RGBA")
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        buf = _io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception:
        b64 = image_to_base64(LOGO_PATH)
        return f"data:image/png;base64,{b64}"


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
    """Render infographics inside dark-themed data panels."""
    if not images:
        return ""

    TYPE_BADGE = {
        "illustration": ("ILLUSTRATION", "#5DADE2"),
        "bar_chart":    ("CHART · BAR",  "#27AE60"),
        "line_chart":   ("CHART · LINE", "#27AE60"),
        "pie_chart":    ("CHART · PIE",  "#8E44AD"),
        "stat_card":    ("DATA · STAT",  accent),
    }
    html = ""
    for img in images:
        b64   = img.get("base64_data_uri", "")
        if not b64:
            continue
        title     = img.get("title", "")
        itype     = img.get("type", "")
        badge_label, badge_color = TYPE_BADGE.get(itype, ("DATA", accent))

        html += f"""
  <div style="background:#0D1117;border:1px solid #1E2A3A;border-radius:20px;
              overflow:hidden;margin:12px 0;box-shadow:0 4px 24px rgba(0,0,0,0.4);
              position:relative;">
    <!-- Top accent line -->
    <div style="height:3px;background:linear-gradient(90deg,{badge_color},{badge_color}44,transparent);"></div>
    <!-- Header row -->
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:14px 20px 10px;">
      <span style="font-family:{mono_font};font-size:9px;font-weight:700;
                   text-transform:uppercase;letter-spacing:2.5px;color:{badge_color};">
        {badge_label}</span>
      <span style="font-family:{mono_font};font-size:11px;color:#F0F0F0;font-weight:600;">
        {title}</span>
    </div>
    <!-- Image -->
    <div style="padding:0 16px 16px;">
      <img src="{b64}" alt="{title}"
           style="width:100%;border-radius:12px;display:block;
                  border:1px solid #1E2A3A;">
    </div>
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
# LAYOUT: TECH  — MR Industries premium editorial dark newsletter
# ══════════════════════════════════════════════════════════════════════════════
def render_tech(content, theme, style, chart_images, citations, date_str):
    import re as _re

    topic     = content.get("topic","")
    headline  = content.get("headline","")
    subhead   = content.get("subheadline","")
    summary   = content.get("summary","")
    sections  = content.get("sections",[])
    key_stats = content.get("key_stats",[])
    citation_map = {c["index"]: c for c in citations}

    accent  = theme["accent"]
    accent2 = theme["accent2"]
    hf = theme["heading_font"]
    bf = theme["body_font"]
    mf = theme["mono_font"]
    nl     = style.get("newsletter_name","Newsletter")
    tagline= style.get("footer_tagline","")
    sender = style.get("sender_name","")

    def _lead(text, n=3):
        parts = _re.split(r'(?<=[.!?])\s+', text.strip())
        return ' '.join(parts[:n])

    orbitron = "'Orbitron', monospace"

    # ── Brand assets ─────────────────────────────────────────────
    logo_b64 = load_brand_logo_b64()
    logo_mast = (
        f'<img src="{logo_b64}" alt="MR Industries" style="height:44px;width:44px;'
        f'object-fit:contain;border-radius:8px;display:block;flex-shrink:0;">'
        if logo_b64 else ''
    )
    logo_foot = (
        f'<img src="{logo_b64}" alt="MR Industries" style="height:36px;width:36px;'
        f'object-fit:contain;border-radius:6px;margin-right:12px;flex-shrink:0;">'
        if logo_b64 else ''
    )

    # ── No hero image — typographic hero only ────────────────────
    pass

    # ── Stats grid ───────────────────────────────────────────────
    stat_accents = [accent, "#8BB8D4", accent2, "#6BB89E"]
    stats_html = ""
    for i, s in enumerate(key_stats[:4]):
        c = stat_accents[i % 4]
        stats_html += (
            f'<div style="background:#111827;border:1px solid #1E2D42;border-radius:10px;'
            f'border-top:3px solid {c};padding:22px 18px;text-align:center;">'
            f'<div class="counter" data-original="{s.get("value","—")}"'
            f' style="font-family:{orbitron};font-size:28px;font-weight:800;color:{c};'
            f'line-height:1.15;letter-spacing:-0.5px;margin-bottom:10px;'
            f'min-height:98px;display:flex;align-items:center;justify-content:center;'
            f'text-shadow:0 0 18px {c}44;">{s.get("value","—")}</div>'
            f'<div style="font-family:\'Roboto Mono\',monospace;font-size:7px;color:#4B607A;'
            f'text-transform:uppercase;letter-spacing:2px;line-height:1.6;">'
            f'{s.get("label","")}</div>'
            f'</div>'
        )

    # ── Brief ────────────────────────────────────────────────────
    brief_text = _lead(summary, 2)

    # ── Section cards ────────────────────────────────────────────
    sects_html = ""
    for i, s in enumerate(sections):
        c   = stat_accents[i % 4]
        all_sentences = _re.split(r'(?<=[.!?])\s+', s.get("body","").strip())
        preview_sents = all_sentences[:2]
        extra_sents   = all_sentences[2:]
        body_html = "".join(
            f'<span style="display:block;margin-bottom:8px;">{sent}</span>'
            for sent in preview_sents
        )
        extra_html = "".join(
            f'<span style="display:block;margin-bottom:8px;">{sent}</span>'
            for sent in extra_sents
        ) if extra_sents else ""
        pills = "".join(
            f'<a href="{citation_map[idx]["url"]}" '
            f'style="display:inline-block;border:1px solid #1E2D42;border-radius:3px;'
            f'padding:3px 10px;font-family:\'Roboto Mono\',monospace;font-size:7px;'
            f'color:{c};letter-spacing:1.5px;text-transform:uppercase;'
            f'margin:2px 4px 2px 0;text-decoration:none;opacity:.6;" '
            f'target="_blank">SRC · {idx}</a>'
            for idx in s.get("citation_indexes",[]) if idx in citation_map
        )
        pulled = key_stats[i] if i < len(key_stats) else None
        pulled_html = ""
        if pulled:
            p_words = pulled.get("label","").split()
            p_top = " ".join(p_words[:4])
            p_bot = " ".join(p_words[4:]) if len(p_words) > 4 else ""
            pulled_html = (
                f'<div style="flex-shrink:0;text-align:right;padding-left:24px;'
                f'border-left:1px solid #1E2D42;min-width:100px;">'
                f'<div style="font-family:{orbitron};font-size:36px;font-weight:800;'
                f'color:{c};line-height:1;letter-spacing:-1px;'
                f'text-shadow:0 0 24px {c}44;">'
                f'{pulled.get("value","")}</div>'
                f'<div style="font-family:\'Roboto Mono\',monospace;font-size:7px;color:#3A5068;'
                f'text-transform:uppercase;letter-spacing:2px;margin-top:8px;'
                f'line-height:1.6;max-width:95px;margin-left:auto;">'
                f'{p_top}{"<br>" + p_bot if p_bot else ""}</div>'
                f'</div>'
            )
        border = "border-bottom:1px solid #0E1829;" if i < len(sections) - 1 else ""
        heading_upper = s.get("heading","").upper()
        sects_html += (
            f'<div class="section-row" style="padding:38px 0;{border}">'
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">'
            f'<span style="font-family:{orbitron};font-size:10px;color:{c};font-weight:900;'
            f'letter-spacing:4px;text-shadow:0 0 12px {c}55;">{str(i+1).zfill(2)}</span>'
            f'<div style="flex:1;height:1px;'
            f'background:linear-gradient(90deg,{c}66,{c}11,transparent);"></div>'
            f'<span style="font-family:\'Roboto Mono\',monospace;font-size:7px;'
            f'color:#2A3D55;letter-spacing:2px;text-transform:uppercase;">Analysis</span>'
            f'</div>'
            f'<div style="display:flex;align-items:flex-start;gap:24px;">'
            f'<div style="flex:1;min-width:0;">'
            f'<h2 style="font-family:\'Oswald\',sans-serif;font-size:24px;font-weight:700;'
            f'color:#E8E8E8;margin-bottom:16px;line-height:1.15;letter-spacing:1.5px;'
            f'text-transform:uppercase;">{heading_upper}</h2>'
            f'<div style="font-family:\'Exo 2\',sans-serif;font-size:13.5px;'
            f'font-weight:300;color:#7A8FA8;line-height:1.9;letter-spacing:0.3px;">'
            f'{body_html}</div>'
            + (
                f'<div class="story-extra" id="extra-{i}"'
                f' style="font-family:\'Exo 2\',sans-serif;font-size:13.5px;'
                f'font-weight:300;color:#7A8FA8;line-height:1.9;letter-spacing:0.3px;">'
                f'{extra_html}</div>'
                f'<button class="expand-btn" id="btn-{i}" onclick="toggleStory({i})">'
                f'Read Full Analysis &#8594;</button>'
                if extra_html else ""
            )
            + (f'<div style="margin-top:12px;">{pills}</div>' if pills else "")
            + f'</div>{pulled_html}</div></div>'
        )

    # ── Data section — pure HTML, no PNG images ───────────────────
    infographic_suggestions = content.get("infographic_suggestions", [])
    non_illus = [s for s in infographic_suggestions if s.get("type") != "illustration"]
    bar_colors = [accent, accent2, "#8BB8D4", "#6BB89E"]

    stat_cards_html = ""
    bar_charts_html = ""

    for item in non_illus:
        t     = item.get("type", "")
        title = item.get("title", "").upper()
        data  = item.get("data", {})

        if t == "stat_card":
            value = data.get("value", "—")
            label = data.get("label", "")
            c = accent if not stat_cards_html else accent2
            stat_cards_html += (
                f'<div style="background:#111827;border:1px solid #1E2D42;border-radius:12px;'
                f'border-top:3px solid {c};padding:30px 24px;">'
                f'<div style="font-family:\'Roboto Mono\',monospace;font-size:7px;color:#3A5068;'
                f'text-transform:uppercase;letter-spacing:3px;margin-bottom:14px;">{title}</div>'
                f'<div style="font-family:{orbitron};font-size:40px;font-weight:900;color:{c};'
                f'line-height:1;letter-spacing:-1px;margin-bottom:14px;'
                f'text-shadow:0 0 28px {c}44;">{value}</div>'
                f'<div style="font-family:\'Exo 2\',sans-serif;font-size:12px;font-weight:300;'
                f'color:#4B607A;line-height:1.6;letter-spacing:0.3px;">{label}</div>'
                f'</div>'
            )

        elif t == "bar_chart":
            labels = data.get("labels", [])
            values = data.get("values", [])
            unit   = data.get("unit", "")
            max_v  = max(values) if values else 1
            bars   = ""
            for j, (lbl, val) in enumerate(zip(labels, values)):
                pct = (val / max_v) * 100
                c   = bar_colors[j % len(bar_colors)]
                bars += (
                    f'<div style="margin-bottom:18px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
                    f'margin-bottom:7px;">'
                    f'<span style="font-family:\'Exo 2\',sans-serif;font-size:12px;'
                    f'font-weight:400;color:#8B9CB6;letter-spacing:0.3px;">{lbl}</span>'
                    f'<span style="font-family:{orbitron};font-size:13px;font-weight:700;'
                    f'color:{c};letter-spacing:-0.5px;">{val}{unit}</span>'
                    f'</div>'
                    f'<div style="background:#0C1220;border-radius:3px;height:8px;overflow:hidden;">'
                    f'<div style="width:{pct:.0f}%;height:100%;border-radius:3px;'
                    f'background:linear-gradient(90deg,{c},{c}66);"></div>'
                    f'</div>'
                    f'</div>'
                )
            bar_charts_html += (
                f'<div style="background:#111827;border:1px solid #1E2D42;border-radius:12px;'
                f'border-top:3px solid {accent2};padding:30px 24px;">'
                f'<div style="font-family:\'Roboto Mono\',monospace;font-size:7px;color:#3A5068;'
                f'text-transform:uppercase;letter-spacing:3px;margin-bottom:20px;">{title}</div>'
                f'{bars}'
                f'</div>'
            )

    data_block = ""
    if stat_cards_html or bar_charts_html:
        inner = ""
        if stat_cards_html:
            inner += (
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;'
                f'margin-bottom:{"12px" if bar_charts_html else "0"};">'
                f'{stat_cards_html}'
                f'</div>'
            )
        if bar_charts_html:
            inner += bar_charts_html

        data_block = (
            f'<div style="padding:44px 0 0;border-top:1px solid #0E1829;">'
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:24px;">'
            f'<span style="font-family:{orbitron};font-size:9px;color:{accent};'
            f'font-weight:700;letter-spacing:4px;text-transform:uppercase;">Data</span>'
            f'<div style="flex:1;height:1px;'
            f'background:linear-gradient(90deg,{accent}66,transparent);"></div>'
            f'</div>'
            f'{inner}'
            f'</div>'
        )

    sources = build_sources_html(citations, mf, accent)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{nl}: {topic}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{theme['fonts']}" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    html{{scrollbar-width:thin;scrollbar-color:{accent} #0C1220;}}
    ::-webkit-scrollbar{{width:4px;}}
    ::-webkit-scrollbar-track{{background:#0C1220;}}
    ::-webkit-scrollbar-thumb{{background:{accent};border-radius:2px;}}
    ::selection{{background:{accent}44;color:#0C1220;}}
    body{{
      background:#0C1220;
      font-family:{bf};
      -webkit-font-smoothing:antialiased;
      color:#E8E8E8;
      padding:0 0 80px;
    }}
    a{{color:inherit;text-decoration:none;}}

    @keyframes fadeInUp{{
      from{{opacity:0;transform:translateY(18px);}}
      to{{opacity:1;transform:translateY(0);}}
    }}
    @keyframes pulse{{
      0%,100%{{opacity:1;}}
      50%{{opacity:.3;}}
    }}
    @keyframes shimmer{{
      0%{{background-position:-200% center;}}
      100%{{background-position:200% center;}}
    }}
    @keyframes heroReveal{{
      from{{opacity:0;transform:scale(1.03);}}
      to{{opacity:1;transform:scale(1);}}
    }}

    .fade{{animation:fadeInUp .65s cubic-bezier(.22,1,.36,1) both;}}
    .d1{{animation-delay:.04s;}} .d2{{animation-delay:.12s;}}
    .d3{{animation-delay:.20s;}} .d4{{animation-delay:.28s;}}
    .d5{{animation-delay:.36s;}} .d6{{animation-delay:.44s;}}
    .d7{{animation-delay:.52s;}}

    .live{{
      display:inline-block;width:7px;height:7px;
      border-radius:50%;background:{accent};
      animation:pulse 2.5s ease infinite;
      box-shadow:0 0 8px {accent}88;
    }}
    .pill{{
      background:linear-gradient(90deg,{accent} 25%,{accent2} 50%,{accent} 75%);
      background-size:200% auto;
      animation:shimmer 3s linear infinite;
      color:#0C1220;
      font-family:'Roboto Mono', monospace;
      font-size:8px;
      padding:4px 14px;
      border-radius:20px;
      letter-spacing:2px;
      text-transform:uppercase;
      font-weight:700;
      display:inline-block;
    }}

    .hero-card{{
      background:#111827;
      border:1px solid #1E2D42;
      border-radius:16px;
      overflow:hidden;
      margin-top:18px;
    }}
    .hero-img{{animation:heroReveal .9s cubic-bezier(.22,1,.36,1) both;}}

    .section-row:hover h2{{color:#FFFFFF;}}
    .section-row h2{{transition:color .2s;}}

    .citation-pill:hover{{
      opacity:1!important;
      border-color:{accent}88!important;
    }}

    .data-img{{
      border-radius:12px;
      border:1px solid #1E2D42;
      display:block;
      width:100%;
    }}

    /* ── Progress bar ── */
    #read-progress{{
      position:fixed;top:0;left:0;height:3px;width:0%;
      background:linear-gradient(90deg,{accent},{accent2});
      z-index:9999;transition:width .08s linear;
      box-shadow:0 0 8px {accent}88;
    }}

    /* ── Expand button ── */
    .expand-btn{{
      background:none;border:1px solid #1E2D42;border-radius:4px;
      color:{accent};font-family:'Roboto Mono',monospace;font-size:8px;
      letter-spacing:2px;text-transform:uppercase;padding:7px 16px;
      cursor:pointer;margin-top:14px;transition:all .2s;
    }}
    .expand-btn:hover{{background:{accent}11;border-color:{accent}66;}}
    .story-extra{{
      overflow:hidden;max-height:0;
      transition:max-height .4s cubic-bezier(.22,1,.36,1),opacity .3s;
      opacity:0;
    }}
    .story-extra.open{{max-height:300px;opacity:1;}}

    /* ── Reactions ── */
    .reaction-btn{{
      background:#111827;border:1px solid #1E2D42;border-radius:8px;
      color:#4B607A;font-family:'Roboto Mono',monospace;font-size:9px;
      letter-spacing:1.5px;text-transform:uppercase;padding:10px 20px;
      cursor:pointer;transition:all .2s;display:inline-flex;
      align-items:center;gap:8px;
    }}
    .reaction-btn:hover{{border-color:{accent}66;color:#E8E8E8;}}
    .reaction-btn.selected{{
      background:{accent}18;border-color:{accent};color:{accent};
      box-shadow:0 0 12px {accent}22;
    }}
  </style>
</head>
<body>
<div id="read-progress"></div>
<div style="max-width:816px;margin:0 auto;padding:0 29px;">

  <!-- ══ MASTHEAD ═══════════════════════════════════════════════ -->
  <header class="fade d1"
    style="display:flex;align-items:center;justify-content:space-between;
           padding:24px 0 22px;">
    <div style="display:flex;align-items:center;gap:14px;">
      {logo_mast}
      <div>
        <span style="font-family:'Oswald',sans-serif;font-size:18px;font-weight:700;
                     color:#E8E8E8;letter-spacing:2px;text-transform:uppercase;
                     display:block;line-height:1;">MR Industries</span>
        <span style="font-family:'Roboto Mono',monospace;font-size:7px;
                     color:#3A5068;letter-spacing:3px;text-transform:uppercase;
                     margin-top:5px;display:block;">Hardware &amp; Machinery</span>
      </div>
    </div>
    <span style="font-family:'Oswald',sans-serif;font-size:11px;font-weight:600;
                 color:#4B607A;letter-spacing:4px;text-transform:uppercase;">{nl}</span>
    <div style="display:flex;align-items:center;gap:8px;">
      <span class="live"></span>
      <span style="font-family:'Roboto Mono',monospace;font-size:9px;color:#3A5068;
                   letter-spacing:1.5px;text-transform:uppercase;">{date_str}</span>
    </div>
  </header>
  <div style="height:1px;background:linear-gradient(90deg,transparent,{accent}44,{accent2}44,transparent);
              margin-bottom:4px;"></div>

  <!-- ══ HERO FEATURE ═══════════════════════════════════════════ -->
  <div class="fade d2" style="
    background:#111827;
    border:1px solid #1E2D42;
    border-radius:16px;
    overflow:hidden;
    margin-top:18px;
    position:relative;">

    <!-- industrial grid pattern -->
    <div style="position:absolute;inset:0;opacity:.04;
      background-image:
        linear-gradient(#E8E8E8 1px,transparent 1px),
        linear-gradient(90deg,#E8E8E8 1px,transparent 1px);
      background-size:32px 32px;"></div>

    <!-- accent side bar -->
    <div style="position:absolute;left:0;top:0;bottom:0;width:4px;
      background:linear-gradient(180deg,{accent},{accent2});"></div>

    <div style="padding:44px 40px 44px 48px;position:relative;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:22px;">
        <span class="pill">Cover Story</span>
        <span style="font-family:'Roboto Mono',monospace;font-size:8px;color:#2D3D55;
                     letter-spacing:3px;text-transform:uppercase;">{topic.upper()}</span>
      </div>
      <h1 style="font-family:'Oswald',sans-serif;font-size:clamp(32px,6vw,54px);
                 font-weight:700;color:#FFFFFF;line-height:1.0;
                 letter-spacing:2px;margin-bottom:20px;text-transform:uppercase;">
        {headline}
      </h1>
      <div style="width:48px;height:3px;
                  background:linear-gradient(90deg,{accent},{accent2});
                  border-radius:2px;margin-bottom:20px;"></div>
      <p style="font-family:'Exo 2',sans-serif;font-size:13.5px;color:#4A6080;
                line-height:1.75;max-width:500px;font-weight:300;
                letter-spacing:0.5px;text-transform:uppercase;">{subhead}</p>
    </div>

  </div>

  <!-- ══ STATS GRID ═════════════════════════════════════════════ -->
  <div class="fade d3"
    style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px;">
    {stats_html}
  </div>

  <!-- ══ THE BRIEF ══════════════════════════════════════════════ -->
  <div class="fade d4"
    style="margin-top:10px;padding:26px 30px;
           border-left:3px solid {accent};
           background:#11182766;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
      <span style="font-family:'Roboto Mono',monospace;font-size:8px;color:{accent};
                   text-transform:uppercase;letter-spacing:3px;font-weight:500;">The Brief</span>
      <div style="flex:1;height:1px;background:linear-gradient(90deg,{accent}33,transparent);"></div>
    </div>
    <p style="font-family:'Exo 2',sans-serif;font-size:14.5px;color:#A8B8CC;
              line-height:1.9;font-weight:300;letter-spacing:0.4px;">{brief_text}</p>
  </div>

  <!-- ══ STORIES ════════════════════════════════════════════════ -->
  <div class="fade d5">
    {sects_html}
  </div>

  <!-- ══ DATA ═══════════════════════════════════════════════════ -->
  {data_block}

  <!-- ══ REACTIONS ════════════════════════════════════════════ -->
  <div class="fade d6" style="margin-top:44px;padding:32px 36px;
    background:#111827;border:1px solid #1E2D42;border-radius:14px;text-align:center;">
    <p style="font-family:'Roboto Mono',monospace;font-size:8px;color:#3A5068;
              text-transform:uppercase;letter-spacing:3px;margin-bottom:20px;">
      Rate This Issue</p>
    <div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap;">
      <button class="reaction-btn" onclick="selectReaction(this)">&#9889; Useful</button>
      <button class="reaction-btn" onclick="selectReaction(this)">&#128296; Inspiring</button>
      <button class="reaction-btn" onclick="selectReaction(this)">&#128640; Share-worthy</button>
      <button class="reaction-btn" onclick="selectReaction(this)">&#128200; Eye-opening</button>
    </div>
    <p id="reaction-thanks" style="font-family:'Exo 2',sans-serif;font-size:12px;
      color:{accent};margin-top:16px;opacity:0;transition:opacity .4s;letter-spacing:1px;">
      Thanks for the feedback.</p>
  </div>

  <!-- ══ FOOTER ════════════════════════════════════════════════ -->
  <footer class="fade d7"
    style="margin-top:48px;padding-top:28px;border-top:1px solid #111C2E;">
    <div style="display:flex;justify-content:space-between;align-items:center;
                margin-bottom:22px;gap:16px;">
      <div style="display:flex;align-items:center;">
        {logo_foot}
        <div>
          <p style="font-family:'Oswald',sans-serif;font-size:16px;font-weight:700;
                    color:#E8E8E8;letter-spacing:.5px;text-transform:uppercase;">{nl}</p>
          <p style="font-family:'Exo 2',sans-serif;font-size:11px;color:#4B607A;
                    margin-top:4px;">{tagline}</p>
        </div>
      </div>
      <span class="pill" style="white-space:nowrap;">{date_str}</span>
    </div>
    {sources}
    <p style="font-family:'Roboto Mono',monospace;font-size:9px;color:#1F3048;
              margin-top:16px;line-height:1.8;letter-spacing:1px;text-transform:uppercase;">
      {sender} &middot; Generated {date_str} &middot;
      <a href="#" style="color:#2E4566;border-bottom:1px solid #1F3048;
                         text-decoration:none;">Unsubscribe</a>
    </p>
  </footer>

</div>

<script>
// ── 1. Reading progress bar ──────────────────────────────────
window.addEventListener('scroll', function() {{
  var el = document.documentElement;
  var pct = (el.scrollTop / (el.scrollHeight - el.clientHeight)) * 100;
  document.getElementById('read-progress').style.width = pct + '%';
}});

// ── 2. Animated stat counters ────────────────────────────────
document.querySelectorAll('.counter').forEach(function(el) {{
  var original = el.dataset.original || el.textContent;
  var match = original.match(/([\d,]+\.?\d*)/);
  if (!match) return;
  var numStr = match[1].replace(/,/g, '');
  var target = parseFloat(numStr);
  if (isNaN(target)) return;
  var hasComma = match[1].indexOf(',') !== -1;
  var isDecimal = numStr.indexOf('.') !== -1;
  var prefix = original.slice(0, original.indexOf(match[1]));
  var suffix = original.slice(original.indexOf(match[1]) + match[1].length);
  var startVal = isDecimal ? Math.floor(target) : 0;
  var startTime = null;
  var duration = 1600;
  function animate(ts) {{
    if (!startTime) startTime = ts;
    var progress = Math.min((ts - startTime) / duration, 1);
    var eased = 1 - Math.pow(1 - progress, 3);
    var current = startVal + eased * (target - startVal);
    var formatted = isDecimal
      ? current.toFixed(1)
      : (hasComma ? Math.floor(current).toLocaleString() : Math.floor(current).toString());
    el.textContent = prefix + formatted + suffix;
    if (progress < 1) requestAnimationFrame(animate);
  }}
  el.textContent = prefix + startVal.toFixed(isDecimal ? 1 : 0) + suffix;
  requestAnimationFrame(animate);
}});

// ── 3. Expandable story sections ─────────────────────────────
function toggleStory(i) {{
  var extra = document.getElementById('extra-' + i);
  var btn   = document.getElementById('btn-' + i);
  if (!extra) return;
  var open = extra.classList.contains('open');
  extra.classList.toggle('open', !open);
  btn.innerHTML = open ? 'Read Full Analysis &#8594;' : '&#8592; Collapse';
}}

// ── 4. Reaction strip ────────────────────────────────────────
function selectReaction(el) {{
  document.querySelectorAll('.reaction-btn').forEach(function(b) {{
    b.classList.remove('selected');
  }});
  el.classList.add('selected');
  var thanks = document.getElementById('reaction-thanks');
  if (thanks) thanks.style.opacity = '1';
}}
</script>
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
            b64  = image_to_base64(fp)
            ext  = os.path.splitext(fp)[1].lower()
            mime = "image/svg+xml" if ext == ".svg" else "image/png"
            chart_images.append({
                "title":          item["title"],
                "type":           item.get("type", ""),
                "base64_data_uri": f"data:{mime};base64,{b64}",
            })

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
