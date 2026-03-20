#!/usr/bin/env python3
"""
generate_infographics.py — Generate charts, stat cards, and AI illustrations.

Usage:
    python tools/generate_infographics.py

Reads:  .tmp/newsletter_content.json
Output: .tmp/infographics/*.png + .tmp/infographics/manifest.json
"""

import base64
import io
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FAL_KEY = os.getenv("FAL_KEY")
INPUT_PATH = ".tmp/newsletter_content.json"
OUTPUT_DIR = ".tmp/infographics"
MANIFEST_PATH = ".tmp/infographics/manifest.json"
STYLE_CONFIG = "config/newsletter_style.json"


def load_theme() -> dict:
    with open(STYLE_CONFIG) as f:
        style = json.load(f)
    colors = style.get("colors", {})
    fonts = style.get("fonts", {})
    return {
        "primary_color": colors.get("primary", "#1a1a2e"),
        "accent_color": colors.get("accent", "#e94560"),
        "background_color": colors.get("background", "#f8f9fa"),
        "text_color": colors.get("text", "#212529"),
        "muted_color": colors.get("muted", "#6c757d"),
        "chart_palette": colors.get("chart_palette", ["#e94560", "#0f3460", "#533483"]),
        "stat_card_bg": colors.get("stat_card_bg", "#1a1a2e"),
        "stat_card_text": colors.get("stat_card_text", "#ffffff"),
        "stat_card_accent": colors.get("stat_card_accent", "#e94560"),
        "font_family": fonts.get("body", "Arial, sans-serif"),
        "heading_font": fonts.get("heading", "Arial, sans-serif"),
    }


def generate_illustration(suggestion: dict, idx: int, theme: dict) -> None:
    """Generate an AI illustration via Pollinations.ai (free, no API key needed)."""
    import urllib.request
    import urllib.parse

    try:
        style_suffix = (
            "flat editorial illustration, no text, no words, no labels, "
            "modern clean design, professional newsletter graphic, "
            "bold colors, high contrast, cinematic lighting"
        )
        prompt = f"{suggestion.get('prompt', suggestion['title'])}. {style_suffix}"
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=630&nologo=true&seed={idx}"

        print(f"  Generating illustration via Pollinations.ai: '{suggestion['title']}'...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            image_bytes = resp.read()

        if len(image_bytes) < 1000:
            raise ValueError("Response too small — likely not an image")

        filename = f"illustration_{idx:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        print(f"  Generated illustration: {filename} ({len(image_bytes)//1024}KB)")
        return filename

    except Exception as e:
        print(f"  Warning: Pollinations.ai failed ({e}). Falling back to stat card.")
        return generate_stat_card(
            {"type": "stat_card", "title": suggestion["title"], "data": {"value": "✦", "label": suggestion["title"]}},
            idx, theme,
        )


def generate_chart(suggestion: dict, idx: int, theme: dict) -> None:
    """Generate a polished matplotlib chart (bar, line, or pie)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    chart_type = suggestion["type"]
    data = suggestion.get("data", {})
    title = suggestion.get("title", "")

    # Rich, distinct palette
    PALETTE = ["#0E86D4", "#E8622A", "#27AE60", "#8E44AD", "#F39C12", "#E74C3C"]
    bg_color = "#FFFFFF"

    labels = data.get("labels", [])
    values = data.get("values", [])
    unit = data.get("unit", "")

    if not labels or not values:
        print(f"  Warning: No data for chart '{title}'. Skipping.")
        return None

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.spines.bottom": False,
        "axes.grid": True,
        "grid.color": "#F0F0F0",
        "grid.linewidth": 1,
        "axes.axisbelow": True,
    })

    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(bg_color)

    if chart_type == "bar_chart":
        x = range(len(labels))
        bars = ax.bar(x, values, color=PALETTE[:len(values)], edgecolor="none",
                      width=0.55, zorder=3)
        # Value labels on top of bars
        for bar, val in zip(bars, values):
            label = f"{val:g}{unit}"
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(values) * 0.02,
                    label, ha="center", va="bottom",
                    fontsize=10, fontweight="bold",
                    color="#1a1a1a")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=10, color="#444")
        ax.set_ylim(0, max(values) * 1.25)
        ax.yaxis.set_visible(False)

    elif chart_type == "line_chart":
        ax.plot(labels, values, color=PALETTE[0], linewidth=3,
                marker="o", markersize=9, markerfacecolor="#FFFFFF",
                markeredgewidth=2.5, zorder=3)
        ax.fill_between(range(len(labels)), values,
                        alpha=0.08, color=PALETTE[0])
        # Point labels
        for i, (lbl, val) in enumerate(zip(labels, values)):
            ax.annotate(f"{val:g}{unit}", (i, val),
                        textcoords="offset points", xytext=(0, 12),
                        ha="center", fontsize=9, fontweight="bold", color=PALETTE[0])
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=10, color="#444")
        ax.yaxis.set_visible(False)
        ax.set_xlim(-0.3, len(labels) - 0.7)

    elif chart_type == "pie_chart":
        wedge_colors = PALETTE[:len(values)]
        wedges, texts, autotexts = ax.pie(
            values, labels=None,
            colors=wedge_colors,
            autopct="%1.0f%%",
            startangle=90,
            pctdistance=0.75,
            wedgeprops={"edgecolor": "white", "linewidth": 2.5},
        )
        for at in autotexts:
            at.set_fontsize(10)
            at.set_fontweight("bold")
            at.set_color("white")
        # Legend
        legend_patches = [mpatches.Patch(color=wedge_colors[i], label=labels[i])
                          for i in range(len(labels))]
        ax.legend(handles=legend_patches, loc="center left",
                  bbox_to_anchor=(1, 0.5), fontsize=9, frameon=False)

    # Title styling
    ax.set_title(title, fontsize=13, fontweight="bold",
                 color="#1a1a1a", pad=16, loc="left")

    # Subtle bottom line
    if chart_type != "pie_chart":
        ax.axhline(0, color="#E0E0E0", linewidth=1)
        ax.tick_params(axis="both", which="both", length=0)

    plt.tight_layout(pad=1.5)

    filename = f"{chart_type}_{idx:02d}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=180, bbox_inches="tight", facecolor=bg_color)
    plt.close()
    print(f"  Generated chart: {filename}")
    return filename


def generate_stat_card(suggestion: dict, idx: int, theme: dict) -> str:
    """Generate a polished stat card via matplotlib (no Pillow overflow issues)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import textwrap

    data    = suggestion.get("data", {})
    value   = str(data.get("value", "—"))
    label   = str(data.get("label", suggestion.get("title", "")))

    CARD_COLORS = ["#0E86D4", "#E8622A", "#27AE60", "#8E44AD"]
    accent = CARD_COLORS[idx % len(CARD_COLORS)]

    fig, ax = plt.subplots(figsize=(4.5, 2.2), facecolor="#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.axis("off")

    # Background card with rounded look via filled rectangle
    card = patches.FancyBboxPatch((0.04, 0.06), 0.92, 0.88,
                                   boxstyle="round,pad=0.02",
                                   linewidth=0, facecolor="#F8F9FA",
                                   transform=ax.transAxes, zorder=1)
    ax.add_patch(card)

    # Top accent bar
    bar = patches.FancyBboxPatch((0.04, 0.88), 0.92, 0.06,
                                  boxstyle="round,pad=0.01",
                                  linewidth=0, facecolor=accent,
                                  transform=ax.transAxes, zorder=2)
    ax.add_patch(bar)

    # Big value
    ax.text(0.5, 0.58, value,
            transform=ax.transAxes,
            fontsize=42, fontweight="bold",
            color=accent, ha="center", va="center", zorder=3)

    # Label — wrap long text
    wrapped = "\n".join(textwrap.wrap(label, width=32))
    ax.text(0.5, 0.22, wrapped,
            transform=ax.transAxes,
            fontsize=9, color="#555555",
            ha="center", va="center",
            fontweight="600",
            linespacing=1.4,
            zorder=3)

    plt.tight_layout(pad=0)
    filename  = f"stat_card_{idx:02d}.png"
    filepath  = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=180, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close()
    print(f"  Generated stat card: {filename}")
    return filename


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
    manifest = []

    for idx, suggestion in enumerate(suggestions):
        chart_type = suggestion.get("type", "")
        filename = None

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
                "type": chart_type,
                "filename": filename,
                "filepath": os.path.join(OUTPUT_DIR, filename),
                "title": suggestion.get("title", ""),
            })

    with open(MANIFEST_PATH, "w") as f:
        json.dump({"infographics": manifest}, f, indent=2)

    print(f"\nInfographics complete: {len(manifest)} generated")
    print(f"Manifest: {MANIFEST_PATH}")
    return manifest


if __name__ == "__main__":
    generate_infographics()
