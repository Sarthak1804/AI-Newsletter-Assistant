#!/usr/bin/env python3
"""
generate_infographics.py — Generate dark-themed charts, stat cards, and AI illustrations.

Illustration priority:
  1. fal.ai FLUX/schnell  (FAL_KEY set)
  2. Pollinations.ai       (free fallback)
  3. Dark stat card        (final fallback)

All Pillow/matplotlib outputs use the newsletter's dark palette so images
integrate seamlessly with the deep-space HTML theme.
"""

import base64
import io
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

FAL_KEY           = os.getenv("FAL_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
INPUT_PATH = ".tmp/newsletter_content.json"
OUTPUT_DIR = ".tmp/infographics"
MANIFEST_PATH = ".tmp/infographics/manifest.json"
STYLE_CONFIG  = "config/newsletter_style.json"
LOGO_PATH     = "brand_assets/Bold Industrial Logo Design for MR.png"

# ── Dark palette (matches render_tech CSS vars) ────────────────────────────────
DARK_BG      = "#020817"
DARK_SURFACE = "#0D1117"
DARK_SURFACE2 = "#111827"
DARK_BORDER  = "#1E2A3A"
ACCENT       = "#E8622A"
ACCENT2      = "#F4D03F"
MUTED        = "#6B7280"
TEXT_DIM     = "#9CA3AF"
TEXT_BRIGHT  = "#F0F0F0"

PALETTE = [ACCENT, "#5DADE2", ACCENT2, "#8E44AD", "#27AE60", "#E74C3C"]


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_theme() -> dict:
    with open(STYLE_CONFIG) as f:
        style = json.load(f)
    colors = style.get("colors", {})
    fonts  = style.get("fonts", {})
    return {
        "primary_color":  colors.get("primary",  "#1a1a2e"),
        "accent_color":   colors.get("accent",   ACCENT),
        "chart_palette":  colors.get("chart_palette", PALETTE),
        "stat_card_bg":   colors.get("stat_card_bg",  DARK_SURFACE),
        "stat_card_text": colors.get("stat_card_text", TEXT_BRIGHT),
        "stat_card_accent": colors.get("stat_card_accent", ACCENT),
        "font_family":    fonts.get("body",    "DejaVu Sans"),
        "heading_font":   fonts.get("heading", "DejaVu Sans"),
    }


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _apply_dark_rcparams():
    """Apply global matplotlib dark theme settings."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family":          "DejaVu Sans",
        "figure.facecolor":     DARK_SURFACE,
        "axes.facecolor":       DARK_SURFACE,
        "axes.edgecolor":       DARK_BORDER,
        "axes.labelcolor":      TEXT_DIM,
        "xtick.color":          TEXT_DIM,
        "ytick.color":          TEXT_DIM,
        "text.color":           TEXT_BRIGHT,
        "grid.color":           DARK_BORDER,
        "grid.linewidth":       0.8,
        "axes.grid":            True,
        "axes.axisbelow":       True,
        "axes.spines.top":      False,
        "axes.spines.right":    False,
        "axes.spines.left":     False,
        "axes.spines.bottom":   False,
    })


# ── Illustration via Claude SVG (primary — always free) ───────────────────────

def generate_illustration_svg(suggestion: dict, idx: int) -> "Optional[str]":
    """
    Generate a dark-themed SVG editorial illustration via OpenRouter LLM (free).
    Uses the same OpenRouter key already used for synthesis — zero extra cost.
    SVGs are infinitely sharp, dark-themed by design, and support CSS animations.
    """
    if not OPENROUTER_API_KEY:
        return None

    import urllib.request as _req
    import json as _json

    topic       = suggestion.get("title", "Technology")
    prompt_text = suggestion.get("prompt", topic)

    system = (
        "You are an expert SVG illustrator specializing in dark editorial design for tech publications. "
        "Output ONLY raw SVG markup — absolutely no explanation, markdown, or code fences. "
        "Start with <svg and end with </svg>. Every element must be valid SVG."
    )

    user_msg = f"""Create a cinematic dark-themed SVG editorial illustration (1200×630px) for the concept: "{prompt_text}"

Hard requirements:
- viewBox="0 0 1200 630" width="1200" height="630"
- Background: deep space dark #020817 with a radial gradient overlay
- NO text, NO labels, NO words — purely visual/abstract
- Color palette: #E8622A (orange glow), #5DADE2 (electric blue), #F4D03F (gold), white at low opacity
- Style: layered geometric shapes, orbital paths, radial bursts, depth from semi-transparent overlays
- Use <defs> for: at least 2 linearGradients, 2 radialGradients, 1 Gaussian blur filter for glow effects
- Add a subtle dot-grid pattern using <pattern> in <defs>
- Minimum 20 SVG elements (circles, ellipses, paths, polygons, rects, lines)
- Include at least 2 animated elements using <animateTransform> (rotate/scale) or <animate> (opacity)
- Add glowing halos around key shapes using the blur filter
- Make it feel like a premium tech magazine spread — cinematic, professional, visually rich"""

    try:
        print(f"  → OpenRouter SVG: '{topic}'...")
        payload = _json.dumps({
            "model":    "google/gemini-2.5-pro",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user_msg},
            ],
            "max_tokens": 6000,
            "temperature": 0.7,
        }).encode()

        request = _req.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "https://github.com/MR-Industries/newsletter",
                "X-Title":       "MR Industries Newsletter",
            },
            method="POST",
        )

        with _req.urlopen(request, timeout=90) as resp:
            result = _json.loads(resp.read())

        svg_text = result["choices"][0]["message"]["content"].strip()

        # Strip markdown fences if model wraps output
        for fence in ("```svg", "```xml", "```"):
            if svg_text.startswith(fence):
                svg_text = svg_text[len(fence):]
                break
        if svg_text.endswith("```"):
            svg_text = svg_text[:-3]
        svg_text = svg_text.strip()

        if not svg_text.startswith("<svg"):
            raise ValueError(f"Response is not SVG (starts with: {svg_text[:60]!r})")

        filename = f"illustration_{idx:02d}.svg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_text)
        print(f"     ✓ {filename} ({len(svg_text)//1024}KB SVG)")
        return filename

    except Exception as e:
        print(f"     ✗ OpenRouter SVG failed: {e}")
        return None


# ── Illustration via OpenRouter (free FLUX models) ─────────────────────────────

def generate_illustration_openrouter(suggestion: dict, idx: int) -> "Optional[str]":
    """
    Generate illustration via OpenRouter image generation endpoint.
    Uses black-forest-labs/flux-schnell:free (no credits needed).
    """
    if not OPENROUTER_API_KEY:
        return None
    try:
        import urllib.request, urllib.parse, json as _json

        style_suffix = (
            "cinematic editorial illustration, no text, no words, no labels, "
            "dark deep-space color palette, navy blacks and electric neon accents, "
            "ultra-detailed professional graphic design, volumetric lighting, "
            "sharp focus, award-winning visual, photorealistic quality"
        )
        prompt = f"{suggestion.get('prompt', suggestion['title'])}. {style_suffix}"

        print(f"  → OpenRouter FLUX: '{suggestion['title']}'...")

        payload = _json.dumps({
            "model": "black-forest-labs/flux-schnell:free",
            "prompt": prompt,
            "width":  1344,
            "height": 768,
        }).encode()

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/images/generations",
            data=payload,
            headers={
                "Authorization":  f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":   "application/json",
                "HTTP-Referer":   "https://github.com/MR-Industries/newsletter",
                "X-Title":        "MR Industries Newsletter",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=90) as resp:
            result = _json.loads(resp.read())

        # Response: {"data": [{"url": "..."}]} or {"data": [{"b64_json": "..."}]}
        item = result["data"][0]
        if "url" in item:
            with urllib.request.urlopen(item["url"], timeout=30) as r:
                image_bytes = r.read()
        elif "b64_json" in item:
            import base64 as _b64
            image_bytes = _b64.b64decode(item["b64_json"])
        else:
            raise ValueError(f"Unexpected response shape: {list(item.keys())}")

        filename = f"illustration_{idx:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        print(f"     ✓ {filename} ({len(image_bytes)//1024}KB)")
        return filename

    except Exception as e:
        print(f"     ✗ OpenRouter failed: {e}")
        return None


def generate_illustration_pollinations(suggestion: dict, idx: int) -> "Optional[str]":
    """Fallback: Pollinations.ai (free, no key)."""
    import urllib.request, urllib.parse
    try:
        style_suffix = (
            "flat editorial illustration, no text, no words, no labels, "
            "dark space aesthetic, navy background, neon accents, "
            "modern professional newsletter graphic, cinematic lighting"
        )
        prompt  = f"{suggestion.get('prompt', suggestion['title'])}. {style_suffix}"
        encoded = urllib.parse.quote(prompt)
        url     = (f"https://image.pollinations.ai/prompt/{encoded}"
                   f"?width=1200&height=630&nologo=true&seed={idx + 42}")

        print(f"  → Pollinations.ai: '{suggestion['title']}'...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            image_bytes = resp.read()

        if len(image_bytes) < 5000:
            raise ValueError("Response too small")

        filename = f"illustration_{idx:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        print(f"     ✓ {filename} ({len(image_bytes)//1024}KB)")
        return filename

    except Exception as e:
        print(f"     ✗ Pollinations failed: {e}")
        return None


def generate_illustration(suggestion: dict, idx: int, theme: dict) -> str:
    """Try OpenRouter SVG → fal.ai → Pollinations → dark stat card fallback."""
    result = generate_illustration_svg(suggestion, idx)
    if result:
        return result

    if OPENROUTER_API_KEY:
        result = generate_illustration_openrouter(suggestion, idx)
        if result:
            return result

    if FAL_KEY:
        try:
            import fal_client
            style_suffix = (
                "cinematic editorial illustration, no text, no words, no labels, "
                "dark deep-space palette, volumetric lighting, ultra-detailed"
            )
            prompt = f"{suggestion.get('prompt', suggestion['title'])}. {style_suffix}"
            print(f"  → fal.ai FLUX: '{suggestion['title']}'...")
            result_fal = fal_client.run(
                "fal-ai/flux/schnell",
                arguments={"prompt": prompt, "image_size": "landscape_16_9",
                            "num_inference_steps": 4, "num_images": 1},
            )
            import urllib.request
            with urllib.request.urlopen(result_fal["images"][0]["url"], timeout=30) as r:
                image_bytes = r.read()
            filename = f"illustration_{idx:02d}.png"
            with open(os.path.join(OUTPUT_DIR, filename), "wb") as f:
                f.write(image_bytes)
            print(f"     ✓ {filename}")
            return filename
        except Exception as e:
            print(f"     ✗ fal.ai failed: {e}")

    result = generate_illustration_pollinations(suggestion, idx)
    if result:
        return result

    print(f"  → Falling back to dark stat card for '{suggestion['title']}'")
    fallback = {"type": "stat_card", "title": suggestion["title"],
                "data": {"value": "✦", "label": suggestion["title"]}}
    return generate_stat_card(fallback, idx, theme)


# ── Dark-themed charts ─────────────────────────────────────────────────────────

def generate_chart(suggestion: dict, idx: int, theme: dict) -> "Optional[str]":
    _apply_dark_rcparams()
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    chart_type = suggestion["type"]
    data       = suggestion.get("data", {})
    title      = suggestion.get("title", "")
    labels     = data.get("labels", [])
    values     = data.get("values", [])
    unit       = data.get("unit", "")

    if not labels or not values:
        print(f"  Warning: No data for chart '{title}'. Skipping.")
        return None

    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=DARK_SURFACE)
    ax.set_facecolor(DARK_SURFACE)
    fig.patch.set_facecolor(DARK_SURFACE)

    if chart_type == "bar_chart":
        x    = np.arange(len(labels))
        bars = ax.bar(x, values,
                      color=[PALETTE[i % len(PALETTE)] for i in range(len(values))],
                      edgecolor="none", width=0.52, zorder=3)

        # Glow-style value labels
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(values) * 0.03,
                    f"{val:g}{unit}",
                    ha="center", va="bottom",
                    fontsize=11, fontweight="bold", color=TEXT_BRIGHT)

        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=10, color=TEXT_DIM)
        ax.set_ylim(0, max(values) * 1.3)
        ax.yaxis.set_visible(False)

    elif chart_type == "line_chart":
        ax.plot(labels, values,
                color=ACCENT, linewidth=2.5,
                marker="o", markersize=8,
                markerfacecolor=DARK_SURFACE, markeredgecolor=ACCENT,
                markeredgewidth=2, zorder=3)
        ax.fill_between(range(len(labels)), values, alpha=0.12, color=ACCENT)

        for i, (lbl, val) in enumerate(zip(labels, values)):
            ax.annotate(f"{val:g}{unit}", (i, val),
                        textcoords="offset points", xytext=(0, 12),
                        ha="center", fontsize=9, fontweight="bold", color=ACCENT)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=10, color=TEXT_DIM)
        ax.yaxis.set_visible(False)
        ax.set_xlim(-0.3, len(labels) - 0.7)

    elif chart_type == "pie_chart":
        wedge_colors = [PALETTE[i % len(PALETTE)] for i in range(len(values))]
        wedges, texts, autotexts = ax.pie(
            values, labels=None,
            colors=wedge_colors,
            autopct="%1.0f%%",
            startangle=90,
            pctdistance=0.72,
            wedgeprops={"edgecolor": DARK_SURFACE, "linewidth": 3},
        )
        for at in autotexts:
            at.set_fontsize(10)
            at.set_fontweight("bold")
            at.set_color(TEXT_BRIGHT)
        legend_patches = [mpatches.Patch(color=wedge_colors[i], label=labels[i])
                          for i in range(len(labels))]
        ax.legend(handles=legend_patches, loc="center left",
                  bbox_to_anchor=(1, 0.5), fontsize=9, frameon=False,
                  labelcolor=TEXT_DIM)

    # Styled title
    ax.set_title(title, fontsize=13, fontweight="bold",
                 color=TEXT_BRIGHT, pad=18, loc="left")

    # Bottom accent line
    if chart_type != "pie_chart":
        ax.axhline(0, color=DARK_BORDER, linewidth=1)
        ax.tick_params(axis="both", which="both", length=0)

    # Top accent bar via figure line
    fig.add_artist(plt.Line2D([0.02, 0.18], [0.97, 0.97],
                              color=ACCENT, linewidth=3, transform=fig.transFigure))

    plt.tight_layout(pad=1.8)
    filename = f"{chart_type}_{idx:02d}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=180, bbox_inches="tight",
                facecolor=DARK_SURFACE, edgecolor="none")
    plt.close()
    print(f"  Generated dark chart: {filename}")
    return filename


# ── Dark-themed stat cards ─────────────────────────────────────────────────────

def generate_stat_card(suggestion: dict, idx: int, theme: dict) -> str:
    """Dark-themed stat card matching the newsletter's space aesthetic."""
    _apply_dark_rcparams()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import textwrap

    data  = suggestion.get("data", {})
    value = str(data.get("value", "—"))
    label = str(data.get("label", suggestion.get("title", "")))

    accent_colors = [ACCENT, "#5DADE2", ACCENT2, "#8E44AD"]
    card_accent   = accent_colors[idx % len(accent_colors)]

    fig, ax = plt.subplots(figsize=(5, 2.6), facecolor=DARK_SURFACE)
    ax.set_facecolor(DARK_SURFACE)
    fig.patch.set_facecolor(DARK_SURFACE)
    ax.axis("off")

    # Outer card border
    border = patches.FancyBboxPatch(
        (0.03, 0.04), 0.94, 0.92,
        boxstyle="round,pad=0.015",
        linewidth=1.5, edgecolor=DARK_BORDER,
        facecolor=DARK_SURFACE2,
        transform=ax.transAxes, zorder=1,
    )
    ax.add_patch(border)

    # Top accent gradient bar (simulated with two rectangles)
    ax.add_patch(patches.FancyBboxPatch(
        (0.03, 0.88), 0.94, 0.08,
        boxstyle="round,pad=0.01",
        linewidth=0, facecolor=card_accent,
        transform=ax.transAxes, zorder=2,
        alpha=0.9,
    ))

    # Subtle dot-grid texture (background pattern)
    for gx in [0.2, 0.35, 0.5, 0.65, 0.8]:
        for gy in [0.25, 0.45, 0.65]:
            ax.plot(gx, gy, "o", color=DARK_BORDER,
                    markersize=2, transform=ax.transAxes,
                    zorder=1, alpha=0.5)

    # Big value number
    ax.text(0.5, 0.58, value,
            transform=ax.transAxes,
            fontsize=46, fontweight="bold",
            color=card_accent, ha="center", va="center",
            zorder=3)

    # Label text
    wrapped = "\n".join(textwrap.wrap(label, width=36))
    ax.text(0.5, 0.2, wrapped,
            transform=ax.transAxes,
            fontsize=9, color=TEXT_DIM,
            ha="center", va="center",
            fontweight="600", linespacing=1.45,
            zorder=3)

    # Corner accent mark
    ax.text(0.92, 0.14, "◈",
            transform=ax.transAxes,
            fontsize=10, color=card_accent,
            ha="center", va="center", alpha=0.4, zorder=3)

    plt.tight_layout(pad=0)
    filename = f"stat_card_{idx:02d}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=180, bbox_inches="tight",
                facecolor=DARK_SURFACE, edgecolor="none")
    plt.close()
    print(f"  Generated dark stat card: {filename}")
    return filename


# ── Main orchestrator ──────────────────────────────────────────────────────────

def generate_infographics() -> list:
    if not os.path.exists(INPUT_PATH):
        sys.exit(f"Error: {INPUT_PATH} not found. Run synthesize.py first.")

    with open(INPUT_PATH) as f:
        content = json.load(f)

    theme = load_theme()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    suggestions = content.get("infographic_suggestions", [])
    if not suggestions:
        print("No infographic suggestions found in content JSON.")
        return []

    print(f"Generating {len(suggestions)} infographic(s)...")
    print("  Illustration engine: OpenRouter SVG (free LLM) → fal.ai → Pollinations")

    manifest = []

    for idx, suggestion in enumerate(suggestions):
        chart_type = suggestion.get("type", "")
        filename   = None

        if chart_type == "illustration":
            filename = generate_illustration(suggestion, idx, theme)
        elif chart_type in ("bar_chart", "line_chart", "pie_chart"):
            filename = generate_chart(suggestion, idx, theme)
        elif chart_type == "stat_card":
            filename = generate_stat_card(suggestion, idx, theme)
        else:
            print(f"  Unknown type '{chart_type}' for '{suggestion.get('title')}'. Skipping.")
            continue

        if filename:
            manifest.append({
                "type":     chart_type,
                "filename": filename,
                "filepath": os.path.join(OUTPUT_DIR, filename),
                "title":    suggestion.get("title", ""),
            })

    with open(MANIFEST_PATH, "w") as f:
        json.dump({"infographics": manifest}, f, indent=2)

    print(f"\nInfographics complete: {len(manifest)} generated")
    print(f"Manifest: {MANIFEST_PATH}")
    return manifest


if __name__ == "__main__":
    generate_infographics()
