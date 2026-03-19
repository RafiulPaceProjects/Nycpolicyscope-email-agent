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

## Next steps (Phase 2)

- [ ] Connect an LLM (Claude API or Ollama) to generate content from `nyc_updates.json`
- [ ] Wire the full pipeline in n8n: read → generate → validate → render → save
- [ ] Add a real news input source (RSS or API)
- [ ] Connect rendered HTML to GHL draft creation
