# NYC PolicyScope Newsletter — Local Setup

## What this project does

Reads sample NYC borough news → validates structured JSON content → renders a complete HTML email preview → saves to `data/output/`.

Everything runs locally. No live APIs or external services required for Phase 1.

---

## Prerequisites

- Python 3.9+
- pip
- Docker Desktop (for n8n, optional for Phase 1)

---

## Quick Start (Python only — no Docker needed)

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the newsletter render

```bash
python scripts/render_newsletter.py
```

### 3. Open the preview

The script prints the output path. Open it in any browser:

```
data/output/newsletter_YYYYMMDD_HHMMSS.html
```

**Expected output:**
- Console prints: `Validation passed.` then `Preview saved: ...`
- HTML file opens as a complete email preview
- All five borough blocks, insight, feature article, tips, and CTA visible

---

## What each file does

| File | Purpose |
|---|---|
| `data/sample/nyc_updates.json` | Raw borough news inputs (replace with real data later) |
| `data/sample/newsletter_content.json` | Structured newsletter content (replace with AI output later) |
| `schemas/newsletter.json` | JSON Schema — all AI output must validate against this |
| `templates/newsletter.html` | Master HTML email template (Jinja2) — do not restructure |
| `scripts/render_newsletter.py` | Reads content JSON → validates → renders HTML |
| `scripts/validate_json.py` | Standalone schema validator for any content JSON |
| `prompts/newsletter_content.txt` | Prompt template for AI content generation |
| `docker/docker-compose.yml` | Runs n8n locally for workflow orchestration |
| `n8n/workflows/newsletter_mvp.json` | Starter n8n workflow (import via n8n UI) |

---

## Validate a content file manually

```bash
python scripts/validate_json.py data/sample/newsletter_content.json
```

**Success output:**
```
VALID: data/sample/newsletter_content.json
  All required fields present and within constraints.
```

---

## Running with custom content

```bash
python scripts/render_newsletter.py --content path/to/my_content.json --output data/output/my_preview.html
```

---

## Starting n8n (optional, Phase 1+)

```bash
cd docker
docker compose up -d
```

Open: http://localhost:5678
Login: `admin` / `nycpolicy2026`

Import the workflow:
1. In n8n UI → Workflows → Import from file
2. Select `n8n/workflows/newsletter_mvp.json`
3. Click "Execute workflow" to run manually

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'jinja2'`**
Run: `pip install -r requirements.txt`

**`ERROR: Schema validation failed`**
Open the content JSON and check the field flagged in the error. The schema at `schemas/newsletter.json` lists all constraints.

**HTML looks wrong in browser**
Email HTML is designed for email clients — some CSS may look different in a browser. This is expected. The rendering is correct for email delivery.

---

---

## Image generation (Google Imagen 2)

Uses Google AI Studio API. Images are raw PNG — **no visible Gemini logo**.

> The visible Gemini logo only appears when using gemini.google.com (web UI).
> API responses return raw PNG bytes with no overlay. SynthID (an invisible
> perceptual watermark) is embedded at the pixel level by Google — it cannot
> be removed without degrading the image, but it is not visible.

### Setup

1. Get an API key from https://aistudio.google.com/app/apikey
2. Set `GOOGLE_AI_API_KEY=your_key` in `.env`

### Generate an image

```bash
python scripts/generate_image.py --prompt "NYC skyline editorial style" --ratio 16:9
```

Output saved to `data/output/images/image_YYYYMMDD_HHMMSS_1.png`

Available ratios: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`

---

## Nanoclaw: Manager Agent (Discord)

Nanoclaw is the manager agent. It runs in Docker, connects to your Discord
server, reviews newsletter content, and triggers n8n workflows via webhook.

### Prerequisites

- Node.js 20+
- A Discord bot ([create one here](https://discord.com/developers/applications))
  - Required permissions: Send Messages, Read Message History
  - Copy the bot token to `.env` as `DISCORD_BOT_TOKEN`
- Copy the channel ID to `.env` as `DISCORD_CHANNEL_ID` (right-click channel → Copy ID in Discord dev mode)

### First-time setup

```bash
# 1. Fill in .env
cp .env.example .env
# Edit .env with your keys

# 2. Clone and build nanoclaw
bash scripts/setup_nanoclaw.sh

# 3. Start all services
cd docker
docker compose up -d
```

### Import n8n workflows

1. Open http://localhost:5678 (login: admin / nycpolicy2026)
2. Workflows → Import from file
3. Import all three files from `n8n/workflows/`:
   - `newsletter_mvp.json`
   - `ghl_fetch_template.json`
   - `generate_images.json`
   - `full_pipeline.json`
4. Activate each webhook workflow (toggle in top-right of workflow)

### Discord commands (talk to @policy)

| Say | What happens |
|---|---|
| `@policy fetch ghl templates` | Fetches email templates from GHL → saves to `data/output/ghl_templates.json` |
| `@policy generate images for NYC skyline` | Generates image via Imagen 2 → saves PNG to `data/output/images/` |
| `@policy run pipeline` | Validates content → generates image → renders HTML preview |
| `@policy validate newsletter_content.json` | Checks file against schema |

### How nanoclaw triggers n8n

Nanoclaw sends a POST request to the n8n webhook URL:

```
POST http://n8n:5678/webhook/newsletter-pipeline
Header: X-Webhook-Token: <N8N_WEBHOOK_TOKEN>
Body: { "content_file": "data/sample/newsletter_content.json" }
```

The `N8N_WEBHOOK_TOKEN` in `.env` must match what's set in the n8n webhook node.

---

## File index (full)

| File | Purpose |
|---|---|
| `data/sample/nyc_updates.json` | Raw borough news inputs |
| `data/sample/newsletter_content.json` | Structured newsletter content |
| `schemas/newsletter.json` | JSON Schema — all output validated against this |
| `templates/newsletter.html` | Master HTML email template (Jinja2) |
| `scripts/render_newsletter.py` | Reads content → validates → renders HTML |
| `scripts/validate_json.py` | Standalone schema validator |
| `scripts/generate_image.py` | Imagen 2 image generation (no logo) |
| `scripts/setup_nanoclaw.sh` | First-time nanoclaw clone + build |
| `prompts/newsletter_content.txt` | AI prompt template |
| `docker/docker-compose.yml` | n8n + nanoclaw Docker services |
| `nanoclaw/groups/nycpolicyscope/CLAUDE.md` | Manager agent instructions |
| `n8n/workflows/newsletter_mvp.json` | Basic manual render workflow |
| `n8n/workflows/ghl_fetch_template.json` | Fetch GHL email templates |
| `n8n/workflows/generate_images.json` | Imagen 2 image generation |
| `n8n/workflows/full_pipeline.json` | End-to-end pipeline |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'jinja2'`**
Run: `pip install -r requirements.txt`

**`ERROR: Schema validation failed`**
Open the content JSON and check the field flagged in the error. See `schemas/newsletter.json` for all constraints.

**`ERROR: GOOGLE_AI_API_KEY environment variable is not set`**
Fill in `.env` with your Google AI Studio key.

**HTML looks wrong in browser**
Email HTML is designed for email clients — some CSS looks different in a browser. Correct for email delivery.

**nanoclaw container won't start**
Check that `bash scripts/setup_nanoclaw.sh` completed without errors. The `nanoclaw/app/` directory must exist and be built.

**n8n webhook returns 401**
Make sure `N8N_WEBHOOK_TOKEN` in `.env` matches the token nanoclaw is sending.

---

## Next steps (Phase 3)

- [ ] Connect LLM to auto-generate content from `nyc_updates.json`
- [ ] Add real news input source (RSS or GHL form trigger)
- [ ] Wire GHL template fetch into the render pipeline
- [ ] Push rendered HTML to GHL as email draft
- [ ] Add weekly schedule trigger in n8n
