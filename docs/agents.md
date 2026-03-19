# NYC PolicyScope Lab — Swarm Agent Guide

This document describes all agents in the swarm: who they are, when to use them,
how to trigger them, and how they work together.

The entire system runs on **OpenAI API** via Codex CLI and nanoclaw.

---

## Swarm Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CODEX CLI (VS Code)                          │
│                                                                  │
│   AGENTS.md (root)      ← master context                        │
│   ├── n8n/AGENTS.md     ← n8n expert                           │
│   ├── nanoclaw/AGENTS.md← nanoclaw expert                       │
│   ├── scripts/AGENTS.md ← builder/coder                         │
│   ├── prompts/AGENTS.md ← prompt engineer                       │
│   ├── templates/AGENTS.md← HTML/email expert                    │
│   ├── schemas/AGENTS.md ← schema validator                      │
│   └── docker/AGENTS.md  ← DevOps/deployment                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DISCORD (via nanoclaw)                        │
│                                                                  │
│   PolicyBot  (NANOCLAW_GROUP=nycpolicyscope) ← manager          │
│   FlowBot    (NANOCLAW_GROUP=n8n-expert)     ← n8n specialist   │
│   BuildBot   (NANOCLAW_GROUP=builder)        ← vibe coder       │
│   DeployBot  (NANOCLAW_GROUP=deployer)       ← infrastructure   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PROMPTFOO (eval framework)                    │
│                                                                  │
│   tests/newsletter-prompt.yaml   ← prompt schema compliance     │
│   tests/nanoclaw-manager.yaml    ← PolicyBot behavior           │
│   tests/nanoclaw-n8n-expert.yaml ← FlowBot behavior             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Codex CLI Agents (AGENTS.md files)

Codex CLI automatically reads the `AGENTS.md` file in your current directory
when you're vibe coding. Switch directories to switch agent context.

| Directory | Agent | Use when you're... |
|---|---|---|
| `/` (root) | Master Orchestrator | Getting project overview, routing to another agent |
| `n8n/` | n8n Expert | Editing workflows, debugging webhook flows |
| `nanoclaw/` | Nanoclaw Expert | Configuring Discord agents, container setup |
| `scripts/` | Builder | Writing/fixing Python pipeline scripts |
| `prompts/` | Prompt Engineer | Editing OpenAI prompts, running evals |
| `templates/` | HTML/Email Expert | Editing the Jinja2 email template |
| `schemas/` | Schema Validator | Adding/changing JSON schema fields |
| `docker/` | DevOps | Docker Compose, VPS deployment |

**How to use:** Open a file in the target directory in VS Code. Codex reads
that directory's `AGENTS.md` as context automatically.

---

## Discord Agents (nanoclaw groups)

Live AI agents in Discord. Only one runs per container instance.
Switch by changing `NANOCLAW_GROUP` in `docker/docker-compose.yml`.

### PolicyBot — Manager (`nycpolicyscope`)
- **Trigger:** `@policy` (or configured `NANOCLAW_TRIGGER`)
- **What it does:** Reviews newsletter content, triggers n8n workflows, reports status
- **Use it for:** Content review, pipeline coordination, workflow triggering
- **Config:** `nanoclaw/groups/nycpolicyscope/CLAUDE.md`

**Workflow commands:**
```
@policy fetch ghl templates
@policy generate images for NYC skyline editorial
@policy run pipeline
@policy validate newsletter_content.json
```

---

### FlowBot — n8n Expert (`n8n-expert`)
- **Trigger:** `@flow` (or configured `NANOCLAW_TRIGGER`)
- **What it does:** Diagnoses n8n failures, explains node configurations, suggests fixes
- **Use it for:** n8n errors, webhook debugging, workflow questions
- **Config:** `nanoclaw/groups/n8n-expert/CLAUDE.md`
- **Switch to:** `NANOCLAW_GROUP=n8n-expert` + restart nanoclaw

---

### BuildBot — Vibe Coder (`builder`)
- **Trigger:** `@build` (or configured `NANOCLAW_TRIGGER`)
- **What it does:** Writes Python scripts, explains code, generates code snippets
- **Use it for:** New scripts, bug fixes in pipeline code, OpenAI integration
- **Config:** `nanoclaw/groups/builder/CLAUDE.md`
- **Switch to:** `NANOCLAW_GROUP=builder` + restart nanoclaw

---

### DeployBot — Infrastructure (`deployer`)
- **Trigger:** `@deploy` (or configured `NANOCLAW_TRIGGER`)
- **What it does:** Docker setup, VPS deployment, env var troubleshooting, GitHub Actions
- **Use it for:** First-time setup, production deployment, container issues
- **Config:** `nanoclaw/groups/deployer/CLAUDE.md`
- **Switch to:** `NANOCLAW_GROUP=deployer` + restart nanoclaw

---

## Running Multiple Discord Agents Simultaneously

To run more than one Discord agent at once, duplicate the nanoclaw service in
`docker/docker-compose.yml`:

```yaml
services:
  nanoclaw-manager:
    # ... (same as nanoclaw)
    container_name: nycpolicyscope-manager
    environment:
      - NANOCLAW_GROUP=nycpolicyscope
      - NANOCLAW_TRIGGER=@policy

  nanoclaw-builder:
    # ... (same as nanoclaw)
    container_name: nycpolicyscope-builder
    environment:
      - NANOCLAW_GROUP=builder
      - NANOCLAW_TRIGGER=@build
```

Each instance needs a different Discord bot token if they post as different bots.

---

## Promptfoo Evals

Run prompt quality tests before committing prompt changes:

```bash
cd promptfoo
npx promptfoo eval          # run all tests
npx promptfoo view          # browser UI for results
```

See `promptfoo/README.md` for full details.

---

## Agent Interaction Flow

Typical weekly newsletter production:

```
1. [Codex CLI in scripts/] → write/fix pipeline script
2. [Codex CLI in prompts/] → iterate newsletter prompt
3. [promptfoo] → run evals, verify prompt quality
4. [Discord @policy] → "validate newsletter_content.json"
5. [Discord @policy] → "run pipeline"
6. [Discord @policy] → reviews HTML output, approves
7. [Discord @policy] → "fetch ghl templates" → push to GHL (Phase 2)
```

---

## Key Env Vars

| Variable | Used by | Description |
|---|---|---|
| `OPENAI_API_KEY` | Codex CLI, nanoclaw, promptfoo | Primary AI key |
| `DISCORD_BOT_TOKEN` | nanoclaw | Discord bot auth |
| `DISCORD_CHANNEL_ID` | nanoclaw | Channel to listen in |
| `NANOCLAW_TRIGGER` | nanoclaw | Trigger word (e.g., `@policy`) |
| `N8N_WEBHOOK_TOKEN` | n8n + nanoclaw | Shared webhook secret |
| `GOOGLE_AI_API_KEY` | n8n + generate_image.py | Imagen 2 image gen |
| `GHL_API_KEY` | n8n | GoHighLevel CRM |

All vars documented in `.env.example`.
