# NYC PolicyScope Newsletter — Local Setup

## What this project does

Reads NYC borough news → AI generates structured newsletter blocks → validates
blocks against schema → renders a complete HTML email preview → saves to
`data/output/`.

Everything runs locally. No live APIs required for Phase 1 (flat mode).
Phase 2 (blocks mode) requires an OpenAI API key.

---

## Prerequisites

- Python 3.9+
- pip
- Docker Desktop (for n8n, optional)
- OpenAI API key (for AI snippet generation)

---

## Quick Start — Python only (no Docker needed)

### Option A: Block-based pipeline (recommended)

This is the new pipeline. Raw news → AI → blocks → render.

```bash
pip install -r requirements.txt

# 1. Validate the sample blocks file
python scripts/validate_blocks.py data/sample/newsletter_blocks.json

# 2. Render from the sample blocks file (no OpenAI needed)
python scripts/render_newsletter.py --content data/sample/newsletter_blocks.json

# 3. Open the preview
# Console prints the output path:
# data/output/newsletter_YYYYMMDD_HHMMSS.html
```

**Expected output:**
- `Detected format: blocks`
- `Validation passed.`
- `Preview saved: data/output/newsletter_*.html`

### Option B: Generate blocks from raw news with OpenAI

```bash
# Set your OpenAI key in .env
echo "OPENAI_API_KEY=sk-..." >> .env

# Generate newsletter blocks from raw news
python scripts/generate_snippets.py --input data/sample/nyc_updates.json

# The output path is printed: data/output/blocks_YYYYMMDD_HHMMSS.json
# Then render it
python scripts/render_newsletter.py --content data/output/blocks_YYYYMMDD_HHMMSS.json
```

**Dry run (see the prompt without calling OpenAI):**
```bash
python scripts/generate_snippets.py --dry-run
```

### Option C: Legacy flat format (backward compatible)

```bash
python scripts/render_newsletter.py --content data/sample/newsletter_content.json
```

This uses the legacy flat schema (`schemas/newsletter.json`). Still fully supported.

---

## File reference

| File | Purpose |
|---|---|
| `data/sample/nyc_updates.json` | Raw borough news input (pipeline entry point) |
| `data/sample/newsletter_blocks.json` | Sample block-format content (new format) |
| `data/sample/newsletter_content.json` | Sample flat content (legacy format) |
| `schemas/blocks.json` | JSON Schema for block-based content (new) |
| `schemas/newsletter.json` | JSON Schema for flat content (legacy, preserved) |
| `templates/newsletter.html` | Jinja2 email template — handles both flat and block context |
| `scripts/generate_snippets.py` | AI snippet generator: raw news → newsletter_blocks.json |
| `scripts/map_blocks.py` | Mapping layer: blocks → template context |
| `scripts/validate_blocks.py` | Block schema validator |
| `scripts/render_newsletter.py` | Validates + renders HTML from either format |
| `scripts/validate_json.py` | Legacy flat schema validator |
| `scripts/generate_image.py` | Imagen 2 image generation |
| `prompts/snippet_generation.txt` | OpenAI prompt for block generation |
| `docker/docker-compose.yml` | n8n + nanoclaw Docker services |
| `n8n/workflows/full_pipeline.json` | End-to-end pipeline (blocks + flat mode) |

---

## Pipeline data flow

```
data/sample/nyc_updates.json          <- raw news input
        |
        v
scripts/generate_snippets.py          <- calls OpenAI
        |
        v
data/output/blocks_TIMESTAMP.json     <- structured newsletter blocks
        |
        v
scripts/validate_blocks.py            <- validates against schemas/blocks.json
        |
        v
scripts/render_newsletter.py          <- detects format, builds context
        |
        v (map_blocks.py for block format)
templates/newsletter.html             <- Jinja2 render
        |
        v
data/output/newsletter_TIMESTAMP.html <- final HTML preview
```

---

## Validate files manually

```bash
# Validate blocks format
python scripts/validate_blocks.py data/sample/newsletter_blocks.json

# Validate legacy flat format
python scripts/validate_json.py data/sample/newsletter_content.json
```

Success output (blocks):
```
VALID: data/sample/newsletter_blocks.json
  9 blocks: news_item, news_item, news_item, news_item, news_item, insight, feature, tips, cta
```

---

## Inspect the template context mapping

```bash
# Show block context (what the template receives in block mode)
python scripts/map_blocks.py data/sample/newsletter_blocks.json

# Show flat context mapping (blocks mapped to legacy vars)
python scripts/map_blocks.py data/sample/newsletter_blocks.json --mode flat
```

---

## Render with custom content

```bash
# Render from any blocks file
python scripts/render_newsletter.py --content path/to/my_blocks.json --output data/output/my_preview.html

# Force format detection
python scripts/render_newsletter.py --content my_file.json --format blocks
python scripts/render_newsletter.py --content my_file.json --format flat
```

---

## Starting n8n (optional, Phase 1+)

```bash
cd docker
docker compose up -d
```

Open: http://localhost:5678
Login: `admin` / `nycpolicy2026`

Import workflows:
1. n8n UI → Workflows → Import from file
2. Select each file from `n8n/workflows/`:
   - `newsletter_mvp.json` (basic manual render)
   - `full_pipeline.json` (full pipeline, blocks + flat mode)
   - `ghl_fetch_template.json` (GHL — Phase 4, placeholder)
   - `generate_images.json` (Imagen 2 image generation)
3. Activate each webhook workflow (toggle in top-right)

### Trigger the pipeline via webhook (blocks mode)

```bash
curl -X POST http://localhost:5678/webhook/newsletter-pipeline \
  -H "X-Webhook-Token: your_token" \
  -H "Content-Type: application/json" \
  -d '{"raw_news_file": "data/sample/nyc_updates.json", "generate_images": true}'
```

### Trigger the pipeline via webhook (flat mode)

```bash
curl -X POST http://localhost:5678/webhook/newsletter-pipeline \
  -H "X-Webhook-Token: your_token" \
  -H "Content-Type: application/json" \
  -d '{"content_file": "data/sample/newsletter_content.json"}'
```

---

## Image generation (Google Imagen 2)

```bash
# Set key in .env
echo "GOOGLE_AI_API_KEY=your_key" >> .env

python scripts/generate_image.py --prompt "NYC skyline editorial style" --ratio 16:9
```

Output: `data/output/images/image_YYYYMMDD_HHMMSS_1.png`

---

## Nanoclaw: Manager Agent (Discord)

Nanoclaw connects to Discord and triggers n8n workflows via webhook.

### First-time setup

```bash
cp .env.example .env
# Edit .env with your keys

bash scripts/setup_nanoclaw.sh

cd docker
docker compose up -d
```

### Discord commands (talk to @policy)

| Say | What happens |
|---|---|
| `@policy generate snippets from nyc_updates.json` | AI generates blocks, validates, renders HTML |
| `@policy run pipeline` | Renders legacy flat content |
| `@policy validate blocks newsletter_blocks.json` | Validates against blocks schema |
| `@policy validate newsletter_content.json` | Validates against flat schema |
| `@policy generate images for NYC skyline` | Imagen 2 PNG generation |
| `@policy fetch ghl templates` | GHL template fetch (Phase 4) |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'jinja2'`**
Run: `pip install -r requirements.txt`

**`ModuleNotFoundError: No module named 'openai'`**
Run: `pip install openai`

**`ERROR: Schema validation failed` (blocks)**
Open the blocks JSON. Run `validate_blocks.py` and check the path shown in error.
See `schemas/blocks.json` for all constraints and block type definitions.

**`ERROR: OPENAI_API_KEY environment variable is not set`**
Fill in `.env` with your OpenAI key or export it in your shell.

**`ERROR: GOOGLE_AI_API_KEY environment variable is not set`**
Fill in `.env` with your Google AI Studio key.

**HTML looks wrong in browser**
Email HTML is designed for email clients — some CSS differs in a browser. Expected.

**n8n webhook returns 401**
`N8N_WEBHOOK_TOKEN` in `.env` must match what nanoclaw sends.

**`map_blocks.py not found` when rendering**
Ensure you're running `render_newsletter.py` from the repo root, or with the
`scripts/` directory on your Python path.

---

## Next steps (Phase roadmap)

- [x] Phase 1: Manual flat rendering (complete)
- [x] Phase 2: Block schema + AI snippet generation (complete)
- [ ] Phase 3: Live news ingestion (RSS / GHL form trigger)
- [ ] Phase 4: GHL publishing — push rendered HTML as email draft
- [ ] Phase 5: Scheduled weekly automation (n8n schedule trigger)
