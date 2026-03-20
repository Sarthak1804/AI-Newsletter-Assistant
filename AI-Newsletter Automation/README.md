# AI Newsletter Assistant

> My first vibe-coded project — built as an Engineer-turned-PM who wanted to see just how fast AI can ship real software.

An end-to-end newsletter automation pipeline. Give it a topic, it does everything else — researches the web, writes the content, generates charts, picks a design theme, renders a beautiful HTML newsletter, and drops it in your Gmail drafts for review.

---

## What it does

```
Topic → Research → Write → Design → Infographics → HTML → Gmail Draft
```

1. **Research** — Pulls the latest news and data via Perplexity API with real citation titles
2. **Synthesize** — Structures content into headline, sections, key stats, and chart suggestions via Gemini 2.5 Pro
3. **Infographics** — Generates polished charts (bar, line, pie) and stat cards via matplotlib
4. **Render** — Builds a fully themed HTML newsletter — layout, fonts, colors, and decorative elements all change based on the topic
5. **Draft** — Saves to Gmail drafts via OAuth2 for review before sending

---

## Themes (auto-detected from topic)

| Topic keywords | Theme | Fonts | Layout style |
|---|---|---|---|
| AI, robotics, LLM, software | **Tech** | Space Grotesk + Space Mono | Dark hero, pixel art, ticker tape |
| EV, climate, travel, nature | **Eco / Travel** | Playfair Display + Lato | Full-bleed photo, editorial pull quotes |
| Finance, crypto, markets, IPO | **Finance** | IBM Plex Serif + Mono | Bloomberg-style, numbered sections |
| Health, cancer, biotech, pharma | **Health** | Inter + Roboto Mono | Clinical report, finding badges |

---

## Stack

| Layer | Tool |
|---|---|
| Research | Perplexity API (`sonar` model) |
| Content synthesis | OpenRouter → Gemini 2.5 Pro |
| Charts & stat cards | matplotlib |
| AI illustrations | fal.ai FLUX.1 (optional) |
| Travel photos | Unsplash (no key needed) |
| Email delivery | Gmail API + OAuth2 |

---

## Setup

**1. Clone & install dependencies**
```bash
git clone https://github.com/Sarthak1804/AI-Newsletter-Assistant.git
cd AI-Newsletter-Assistant
pip install -r requirements.txt
```

**2. Add API keys to `.env`**
```
PERPLEXITY_API_KEY=your_key
OPENROUTER_API_KEY=your_key
GEMINI_API_KEY=your_key        # optional, for AI illustrations
FAL_KEY=your_key               # optional, for FLUX illustrations
```

**3. Set up Gmail OAuth**
- Go to [Google Cloud Console](https://console.cloud.google.com) → Enable Gmail API
- Create OAuth credentials (Desktop app) → download as `credentials.json`
- Add yourself as a test user under OAuth consent screen

**4. Configure newsletter style**

Edit `config/newsletter_style.json`:
```json
{
  "newsletter_name": "Your Newsletter",
  "sender_email": "you@gmail.com",
  "model": "google/gemini-2.5-pro"
}
```

Edit `config/recipients.json` with your recipient list.

---

## Run

```bash
# Full pipeline
python3 tools/research.py "your topic here"
python3 tools/synthesize.py --tone analytical --length medium
python3 tools/generate_infographics.py
python3 tools/render_html.py
python3 tools/preview.py          # review in browser
python3 tools/send_email.py       # saves as Gmail draft

# Send immediately (skip draft)
python3 tools/send_email.py --send
```

---

## Project structure

```
tools/
  research.py              # Perplexity API research
  synthesize.py            # LLM content structuring
  generate_infographics.py # Charts + AI illustrations
  render_html.py           # Themed HTML renderer
  preview.py               # Browser preview
  send_email.py            # Gmail draft/send
config/
  newsletter_style.json    # Theme, model, sender config
  recipients.json          # Recipient groups
workflows/
  newsletter.md            # Full SOP and validation gates
```

---

## Built with

**Claude Code** (Sonnet 4.6) — this entire project was vibe-coded in a single session. I'm a 4-year engineer turned Product Manager, and I built this to test just how fast AI-assisted development can move. Turns out: very fast.

---

## What's next

- [ ] Hugging Face free tier for AI illustrations
- [ ] Weekly scheduling via cron
- [ ] Multi-recipient group support
- [ ] Topic deduplication log
