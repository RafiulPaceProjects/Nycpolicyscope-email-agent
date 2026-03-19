# NYC PolicyScope Lab

NYC PolicyScope Lab is a modular newsletter generation system for NYC policy,
housing, transit, and community news. The pipeline ingests raw borough news,
uses AI to generate structured snippet blocks, validates those blocks against
a schema, maps them into an HTML template, and produces a complete email-safe
newsletter preview.

---

## Project overview

### Purpose

The goal is a reusable, schema-first pipeline where:

1. Raw news items come in as JSON
2. AI (OpenAI) generates structured newsletter snippet blocks
3. Blocks are validated against a JSON schema
4. Blocks are mapped into predefined template sections
5. HTML is rendered safely with Jinja2
6. The result is ready for preview and (later) publishing to GoHighLevel

### Pipeline data flow

```
data/sample/nyc_updates.json          <- raw news input
        |
        v
scripts/generate_snippets.py          <- OpenAI → structured blocks
        |
        v
data/output/blocks_TIMESTAMP.json     <- newsletter_blocks.json
        |
        v
scripts/validate_blocks.py            <- validates schemas/blocks.json
        |
        v
scripts/render_newsletter.py          <- auto-detects format, maps context
        |
        v (map_blocks.py)
templates/newsletter.html             <- Jinja2, block-aware + legacy
        |
        v
data/output/newsletter_TIMESTAMP.html <- HTML email preview
```

### Major components

| Component | Role |
|---|---|
| `scripts/generate_snippets.py` | AI snippet generator: raw news → newsletter_blocks.json |
| `scripts/map_blocks.py` | Mapping layer: converts block format to Jinja2 context |
| `scripts/validate_blocks.py` | Block schema validator |
| `scripts/render_newsletter.py` | Format-aware renderer: flat and block modes |
| `templates/newsletter.html` | Email-safe Jinja2 template: block-aware + legacy flat |
| `schemas/blocks.json` | Block-based content schema (new) |
| `schemas/newsletter.json` | Flat content schema (legacy, preserved) |
| `prompts/snippet_generation.txt` | OpenAI prompt template for block generation |
| `n8n/workflows/` | Pipeline orchestration workflows |
| `nanoclaw/` | Discord-facing agent layer for triggering and reviewing |
| `docker/` | Docker Compose for n8n and nanoclaw services |

---

## Quick start

See [docs/setup.md](docs/setup.md) for the full walkthrough.

### Local Python-only (no Docker, no OpenAI)

```bash
pip install -r requirements.txt

# Render from sample blocks file (no API key needed)
python scripts/render_newsletter.py --content data/sample/newsletter_blocks.json

# Or from legacy flat content
python scripts/render_newsletter.py --content data/sample/newsletter_content.json
```

### AI-powered snippet generation

```bash
# Requires OPENAI_API_KEY in .env
python scripts/generate_snippets.py --input data/sample/nyc_updates.json
python scripts/render_newsletter.py --content data/output/blocks_LATEST.json
```

### Docker + n8n orchestration

```bash
cp .env.example .env  # fill in your keys
cd docker
docker compose up -d
# Open http://localhost:5678 and import workflows from n8n/workflows/
```

---

## Content formats

### Block format (new — `newsletter_blocks.json`)

```json
{
  "meta": {
    "subject_line": "NYC PolicyScope Weekly: ...",
    "preview_text": "...",
    "template": "newsletter"
  },
  "blocks": [
    { "type": "news_item", "borough": "Manhattan", "body": "..." },
    { "type": "insight", "body": "..." },
    { "type": "feature", "title": "...", "body": "..." },
    { "type": "tips", "items": ["...", "..."] },
    { "type": "cta", "body": "..." }
  ]
}
```

Block types: `news_item`, `insight`, `feature`, `tips`, `cta`, `links`, `event`, `hero`

### Flat format (legacy — `newsletter_content.json`)

```json
{
  "subject_line": "...",
  "preview_text": "...",
  "nyc_updates": [{"borough": "Manhattan", "body": "..."}],
  "main_insight": "...",
  "feature_title": "...",
  "feature_body": "...",
  "quick_tips": ["..."],
  "cta_text": "..."
}
```

Both formats are fully supported. The renderer auto-detects which to use.

---

## Current status / roadmap

| Phase | Status | Description |
|---|---|---|
| Phase 1 | ✅ Complete | Manual flat rendering, local files, HTML preview |
| Phase 2 | ✅ Complete | Block schema, AI snippet generation, block-aware template |
| Phase 3 | ⏳ Planned | Live news ingestion (RSS / GHL form trigger) |
| Phase 4 | ⏳ Planned | GoHighLevel publishing — push HTML as email draft |
| Phase 5 | ⏳ Planned | Scheduled weekly automation via n8n |

---

## Architecture notes

**Schema-first.** All content validates against JSON Schema before rendering.
Flat content uses `schemas/newsletter.json`. Block content uses `schemas/blocks.json`.

**Format-aware renderer.** `render_newsletter.py` auto-detects flat vs block
format and selects the right schema and context mapping.

**Composable blocks.** The `blocks` array is ordered and rendered in sequence.
news_item blocks are grouped automatically into the NYC Quick Updates section.
New block types (`event`, `links`, `hero`) extend the template without
modifying existing sections.

**Backward compatible.** The legacy flat pipeline still works unchanged.
`schemas/newsletter.json` and the flat rendering path are preserved.

**GHL publishing is Phase 4.** `n8n/workflows/ghl_fetch_template.json` is a
placeholder. It fetches GHL templates but does not yet push rendered HTML.
Wire this in Phase 4 after the render pipeline is proven in production.

**No shell injection.** All user-controlled strings passed to shell commands
are sanitized in n8n Function nodes before use in `executeCommand` steps.
Python scripts never use `subprocess` with `shell=True` and user input.
