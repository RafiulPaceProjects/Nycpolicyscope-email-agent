# NYC PolicyScope Lab — Codex Agent Orchestrator

You are the master coding agent for **NYC PolicyScope Lab**, an automated
weekly newsletter pipeline for NYC policy, housing, transit, and community news.

All AI calls in this system run through **OpenAI API** (Codex CLI).
Do not assume Anthropic/Claude anywhere in code you write.

---

## Project Goal

Build and maintain an automated pipeline that:
1. Ingests NYC borough news updates (JSON)
2. Generates structured newsletter content via OpenAI
3. Validates content against a strict JSON schema
4. Renders an HTML email via Jinja2 template
5. Generates images via Google Imagen 2
6. Pushes the draft to GoHighLevel (GHL) — Phase 2
7. Orchestrates everything via n8n workflows triggered from Discord (nanoclaw)

**Current phase:** MVP — manual trigger, local files, no live news API yet.

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI / LLM | OpenAI API (gpt-4o, o4-mini via Codex CLI) |
| Workflow orchestration | n8n (self-hosted, Docker) |
| Discord bot / agent | nanoclaw (TypeScript container) |
| Image generation | Google Imagen 2 (via AI Studio API) |
| Email CRM | GoHighLevel (GHL) |
| Scripting | Python 3 (render, validate, image gen) |
| Templates | Jinja2 HTML |
| Containerization | Docker Compose |

---

## Directory Map — Sub-Agent Routing

When working in a specific directory, that directory's `AGENTS.md` provides
deep specialized context. Route your work accordingly:

| Directory | Sub-Agent | Expertise |
|---|---|---|
| `n8n/` | n8n Expert | Workflows, webhooks, node configs |
| `nanoclaw/` | Nanoclaw Expert | Discord bot, group config, container |
| `scripts/` | Builder | Python pipeline scripts |
| `prompts/` | Prompt Engineer | Schema-strict prompts, evals |
| `templates/` | Email/HTML Expert | Jinja2, email-safe CSS |
| `schemas/` | Validator | JSON Schema draft-07 |
| `docker/` | DevOps | Docker Compose, deployment |
| `promptfoo/` | Prompt Engineer | Promptfoo evals (run here) |

---

## Key Files

```
AGENTS.md                          ← you are here
.env.example                       ← all env vars documented here
.env                               ← never commit this

data/sample/nyc_updates.json       ← input: raw borough news
data/sample/newsletter_content.json ← input: structured content
schemas/newsletter.json            ← strict JSON schema for content
prompts/newsletter_content.txt     ← OpenAI prompt template (uses {{ updates }})
templates/newsletter.html          ← Jinja2 email template
scripts/render_newsletter.py       ← renders HTML from content JSON
scripts/validate_json.py           ← validates JSON against schema
scripts/generate_image.py          ← Imagen 2 image generation
scripts/setup_nanoclaw.sh          ← first-run nanoclaw setup

n8n/workflows/newsletter_mvp.json  ← Phase 1: manual trigger, local files
n8n/workflows/full_pipeline.json   ← webhook-triggered full pipeline
n8n/workflows/ghl_fetch_template.json ← fetches GHL email templates
n8n/workflows/generate_images.json ← image generation workflow

nanoclaw/groups/nycpolicyscope/CLAUDE.md ← manager agent (PolicyBot)
nanoclaw/groups/n8n-expert/CLAUDE.md     ← n8n specialist agent
nanoclaw/groups/builder/CLAUDE.md        ← vibe coder agent
nanoclaw/groups/deployer/CLAUDE.md       ← deployment agent

docker/docker-compose.yml          ← n8n + nanoclaw services
promptfoo/promptfoo.yaml           ← prompt eval config
docs/agents.md                     ← human guide to the swarm
```

---

## Env Vars (critical ones)

```
OPENAI_API_KEY         ← primary AI key (Codex CLI + any OpenAI calls in code)
GOOGLE_AI_API_KEY      ← Imagen 2 image generation
GHL_API_KEY            ← GoHighLevel CRM
GHL_LOCATION_ID        ← GHL sub-account ID
DISCORD_BOT_TOKEN      ← nanoclaw Discord bot
DISCORD_CHANNEL_ID     ← Discord channel nanoclaw listens in
N8N_BASE_URL           ← n8n instance (default: http://localhost:5678)
N8N_WEBHOOK_TOKEN      ← shared secret for webhook auth
```

---

## Coding Rules

1. **OpenAI only** — All LLM calls use `openai` Python SDK or Codex CLI.
   Do not write code that imports `anthropic`.
2. **Schema-first** — Any content generation must validate against
   `schemas/newsletter.json` before use.
3. **No shell injection** — Shell commands in n8n use sanitized inputs.
   Never interpolate user text directly into command strings.
4. **File paths** — Python scripts use `pathlib.Path`, not raw strings.
5. **Env vars** — Always load from `.env` via `python-dotenv`. Never hardcode.
6. **Test locally first** — Run `python scripts/validate_json.py` and
   `python scripts/render_newsletter.py` before touching n8n workflows.
7. **Email-safe HTML** — Inline CSS only in `templates/newsletter.html`.
   No external stylesheets. No JavaScript.
8. **Commit scope** — One concern per commit. Don't bundle unrelated changes.

---

## Phase Roadmap

| Phase | Status | Description |
|---|---|---|
| 1 — MVP | ✅ Done | Manual trigger, local files, HTML preview |
| 2 — AI Content Gen | 🔄 Next | OpenAI generates content from live news |
| 3 — Live News Feed | ⏳ Planned | Replace sample JSON with real news API |
| 4 — GHL Publishing | ⏳ Planned | Push rendered HTML to GHL as email draft |
| 5 — Scheduling | ⏳ Planned | Weekly cron via n8n, GitHub Actions |

---

## Quick Commands

```bash
# Validate content JSON
python scripts/validate_json.py data/sample/newsletter_content.json

# Render HTML preview
python scripts/render_newsletter.py --content data/sample/newsletter_content.json

# Generate test image
python scripts/generate_image.py --prompt "NYC skyline" --ratio 16:9 --count 1 --json

# Run promptfoo evals
cd promptfoo && npx promptfoo eval

# Start local stack
cd docker && docker compose up -d

# Check n8n
open http://localhost:5678
```

---

## What NOT to do

- Do not redesign `templates/newsletter.html` without being asked
- Do not add new schema fields without updating `schemas/newsletter.json`
- Do not commit `.env`, API keys, or credentials
- Do not push generated HTML files in `data/output/`
- Do not change nanoclaw group configs without updating `docs/agents.md`
