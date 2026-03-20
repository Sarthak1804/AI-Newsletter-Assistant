# Newsletter Automation Workflow

## Objective

Generate a fully researched, designed, and delivered HTML newsletter on any topic. The output is emailed to the user's inbox.

## Required Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `topic` | Yes | — | The newsletter subject (e.g. "breakthroughs in fusion energy 2025") |
| `tone` | No | `analytical` | `analytical` / `casual` / `executive` |
| `length` | No | `medium` | `short` (~400 words) / `medium` (~700 words) / `long` (~1000 words) |
| `recency` | No | `month` | `day` / `week` / `month` / `year` |
| `recipient` | No | `GMAIL_DEFAULT_RECIPIENT` | Override email recipient |

## Pre-Flight Checks

Before starting, verify:

1. **API keys in `.env`:**
   - `ANTHROPIC_API_KEY` — for synthesis and HTML generation
   - `PERPLEXITY_API_KEY` — for research
   - `GEMINI_API_KEY` — for AI illustrations (optional; falls back to stat cards if missing)
   - `GMAIL_DEFAULT_RECIPIENT` — recipient email address

2. **OAuth files exist:**
   - `credentials.json` — Google OAuth client credentials
   - `token.json` — will be created on first Gmail run; must include `gmail.send` scope

3. **Directories exist:** Create if missing:
   ```bash
   mkdir -p .tmp/infographics
   ```

4. **Clear stale files** from previous run:
   ```bash
   rm -f .tmp/research_raw.json .tmp/newsletter_content.json .tmp/newsletter_final.html .tmp/infographics/*.png .tmp/infographics/manifest.json
   ```

5. **Install dependencies** if first run:
   ```bash
   pip install -r requirements.txt
   ```

---

## Pipeline Steps

### Step 1: Research

```bash
python tools/research.py "YOUR TOPIC HERE" --recency month
```

**Validation gate — check `.tmp/research_raw.json`:**
- `citation_count` ≥ 3
- `summary` is non-empty and substantive (not just a few sentences)

**If validation fails:** Retry with a broader or more specific query:
```bash
python tools/research.py "BROADER TOPIC" --recency year
```

If still thin after retry, inform the user: "Research returned fewer than 3 sources. The newsletter may lack citations. Proceed anyway?"

---

### Step 2: Synthesize Content

```bash
python tools/synthesize.py --tone analytical --length medium
```

**Validation gate — check `.tmp/newsletter_content.json`:**
- `sections` array has 3–4 items, each with non-empty `body`
- `key_stats` array: every item has a `citation_index` that exists in `citations`
- `infographic_suggestions` array has at least 2 items

**If invalid stats found:** The script automatically removes uncited stats and prints a warning. Review the warning output and confirm the remaining stats are acceptable.

**If sections are thin:** Re-run with `--length long` or re-run research with `--recency year` for more content.

---

### Step 3: Generate Infographics

```bash
python tools/generate_infographics.py
```

**Validation gate — inspect `.tmp/infographics/`:**
- Open each PNG file and visually confirm:
  - Illustrations: No text or labels visible in the image (Gemini sometimes adds these despite instructions). If text is visible, the type automatically falls back to a stat card — this is acceptable.
  - Charts: Data is readable, labels are not clipped, colors look good.
  - Stat cards: Numbers and labels are legible, layout is centered.

**If Gemini is not configured:** All illustration slots fall back to Pillow stat cards. This is acceptable for a text-focused newsletter.

---

### Step 4: Render HTML

```bash
python tools/render_html.py
```

**Validation gate — check `.tmp/newsletter_final.html`:**
- File exists and is non-empty (should be 50KB+ with images)
- Open the file to spot-check: no obviously broken tags, no "[object Object]" strings, no raw JSON visible

---

### Step 5: Preview — HARD STOP ✋

```bash
python tools/preview.py
```

This opens the newsletter in your browser. **Do not proceed to send until the user has explicitly approved.**

Ask the user:
> "The newsletter preview is now open in your browser. Please review it and let me know:
> 1. Does the layout and design look good?
> 2. Is the content accurate and well-written?
> 3. Are the infographics rendering correctly?
>
> Reply 'send it' to deliver, or describe any changes needed."

**If changes are needed:**
- Content changes (headlines, sections, stats) → Edit `.tmp/newsletter_content.json` manually or re-run `synthesize.py` with adjusted parameters, then re-run `render_html.py`
- Layout changes → Re-run `render_html.py` (Claude will regenerate the HTML)
- Infographic changes → Re-run `generate_infographics.py` for specific types, then `render_html.py`

---

### Step 6: Send Email

```bash
python tools/send_email.py
```

Or to a custom recipient:
```bash
python tools/send_email.py --to other@example.com
```

**First-time Gmail auth:** A browser window will open asking you to authorize Gmail access. Grant `gmail.send` permission. After authorization, `token.json` is updated and future runs are automatic.

**Confirmation:** Script prints the message ID and recipient on success.

---

## Edge Cases

| Situation | Action |
|---|---|
| Perplexity returns 0 citations | Check API key, then retry with year recency. If still failing, check Perplexity API status. |
| Perplexity API timeout | Retry once after 30 seconds. If still failing, report to user. |
| Gemini content policy block | Script automatically falls back to Pillow stat card for that slot. Acceptable. |
| premailer fails during HTML render | Script falls back to raw Claude-generated HTML with a warning. Usually fine — Claude already generates mostly inline CSS. |
| Gmail OAuth scope error | Delete `token.json` and re-run `send_email.py`. A new browser auth flow will request the correct scope. |
| HTML file >100KB | This may cause Gmail to clip the email. Consider `--length short` or removing one infographic. |

---

## Cost Reference

| Step | Cost per run |
|---|---|
| Perplexity research (sonar) | ~$0.001 |
| Claude synthesis (claude-sonnet-4-6, ~2K tokens) | ~$0.003 |
| Gemini Imagen (1-2 illustrations) | Free tier (60 images/min) |
| Claude HTML render (claude-sonnet-4-6, ~6K tokens) | ~$0.009 |
| Gmail send | Free |
| **Total** | **~$0.013 per newsletter** |

---

## Example Run

```bash
# Full pipeline for a newsletter on AI regulation
python tools/research.py "AI regulation and governance 2025" --recency month
python tools/synthesize.py --tone executive --length medium
python tools/generate_infographics.py
python tools/render_html.py
python tools/preview.py
# [user approves]
python tools/send_email.py
```
