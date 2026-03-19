# NYC PolicyScope Lab

NYC PolicyScope Lab is an automated newsletter pipeline for NYC policy, housing, transit, and community news. The project is designed to ingest borough-level news updates, turn them into structured newsletter content, validate that content against a strict JSON schema, render an email-safe HTML newsletter, generate supporting images, and orchestrate the workflow through n8n and nanoclaw.

## Project overview

### Purpose

The goal of NYC PolicyScope Lab is to provide a repeatable, schema-first workflow for producing a weekly NYC newsletter draft. The long-term plan is to connect live news ingestion, OpenAI-powered content generation, Google Imagen 2 image generation, and GoHighLevel publishing into one orchestrated system.

### Current MVP scope

The current MVP focuses on local, file-based workflows:

- use sample JSON files as the source of borough news and newsletter content
- validate newsletter content against `schemas/newsletter.json`
- render an HTML email preview from structured JSON with Jinja2
- support local image generation with Google Imagen 2
- provide n8n workflows for manual execution and early automation experiments
- support Discord-triggered orchestration through nanoclaw as the manager agent layer

This phase is intentionally limited to manual triggering, local files, and HTML preview generation before moving to live feeds and CRM publishing.

### Major components

| Component | Role |
| --- | --- |
| `scripts/` | Python utilities for validation, HTML rendering, image generation, and local setup helpers |
| `templates/` | Jinja2 email templates for the newsletter HTML output |
| `schemas/` | JSON Schema definitions that enforce the newsletter content structure |
| `n8n/` | Workflow definitions for manual runs, image generation, template fetching, and full pipeline orchestration |
| `nanoclaw/` | Discord-facing agent configuration and group instructions for triggering and coordinating workflows |
| `docker/` | Docker Compose setup for local orchestration services such as n8n and nanoclaw |

## Architecture

At a high level, the project works as a staged content pipeline:

1. **JSON news input**  
   Raw NYC updates begin as JSON files such as `data/sample/nyc_updates.json`, and structured newsletter payloads are stored in `data/sample/newsletter_content.json`.
2. **Schema validation**  
   Newsletter content is validated against `schemas/newsletter.json` so downstream steps only operate on predictable, approved structure.
3. **Jinja2 rendering**  
   `scripts/render_newsletter.py` combines validated content with `templates/newsletter.html` to produce an email-safe HTML newsletter preview.
4. **Imagen image generation**  
   `scripts/generate_image.py` can generate editorial imagery with Google Imagen 2 for use in the newsletter workflow.
5. **n8n orchestration**  
   Workflows in `n8n/workflows/` coordinate the pipeline steps for manual MVP runs and future webhook-based automation.
6. **nanoclaw Discord trigger flow**  
   nanoclaw serves as the Discord-facing manager layer that can receive commands, trigger n8n webhooks, and coordinate newsletter pipeline actions.

## Quick start

For a more detailed walkthrough, see [docs/setup.md](docs/setup.md).

### Local Python-only use

Use this path if you want to validate and render the newsletter locally without starting Docker or n8n.

#### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Validate the sample newsletter content

```bash
python scripts/validate_json.py data/sample/newsletter_content.json
```

#### 3. Render an HTML preview

```bash
python scripts/render_newsletter.py --content data/sample/newsletter_content.json
```

The rendered file is written to `data/output/` and can be opened in a browser for preview.

#### 4. Optional: generate a test image

```bash
python scripts/generate_image.py --prompt "NYC skyline editorial style" --ratio 16:9 --count 1 --json
```

Set `GOOGLE_AI_API_KEY` in `.env` before running image generation.

### Docker and n8n setup

Use this path if you want the local orchestration stack for n8n and nanoclaw.

#### 1. Create and fill in your environment file

```bash
cp .env.example .env
```

Add the required values such as `OPENAI_API_KEY`, `GOOGLE_AI_API_KEY`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`, and `N8N_WEBHOOK_TOKEN`.

#### 2. Start the local services

```bash
cd docker
docker compose up -d
```

#### 3. Open n8n

Visit <http://localhost:5678> and import the workflows from `n8n/workflows/` as needed.

#### 4. Optional: prepare nanoclaw

```bash
bash scripts/setup_nanoclaw.sh
```

This helps prepare the nanoclaw side for Discord-triggered workflow execution.

## Current status / roadmap

The project is currently in **Phase 1 — MVP**:

- ✅ Manual trigger flow
- ✅ Local sample files for input content
- ✅ HTML newsletter preview generation
- 🔄 Next: OpenAI-driven content generation from live news inputs
- ⏳ Planned: live news ingestion
- ⏳ Planned: GoHighLevel draft publishing
- ⏳ Planned: scheduled automation through n8n and related tooling

In short, the current repository is ready for local validation, rendering, and orchestration experiments, while the next phases expand toward fully automated newsletter generation and publishing.
