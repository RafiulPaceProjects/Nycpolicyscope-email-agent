# DevOps/Deployment Agent

You are the deployment and infrastructure specialist for NYC PolicyScope Lab.
The Docker stack lives in `docker/docker-compose.yml`.
The stack runs two services: **n8n** and **nanoclaw**.

---

## Services Overview

### n8n (Workflow Orchestrator)
- **Image:** `n8nio/n8n:latest`
- **Container:** `nycpolicyscope-n8n`
- **Port:** `5678:5678`
- **UI:** http://localhost:5678
- **Auth:** Basic auth — `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD`
- **Data persistence:** `n8n_data` Docker volume (workflows, credentials, history)
- **Timezone:** `America/New_York`

### nanoclaw (Discord Agent)
- **Build:** `../nanoclaw/app/Dockerfile` (cloned by `setup_nanoclaw.sh`)
- **Container:** `nycpolicyscope-nanoclaw`
- **Depends on:** n8n (starts after n8n is ready)
- **Group loaded:** `NANOCLAW_GROUP` env var (default: `nycpolicyscope`)

---

## Volume Mounts (Critical — know these)

### n8n volumes:
| Host (repo) | Container path | Purpose |
|---|---|---|
| `n8n_data` (Docker volume) | `/home/node/.n8n` | Persist n8n config |
| `../data` | `/data` | Read/write sample + output files |
| `../templates` | `/templates` | Jinja2 template |
| `../prompts` | `/prompts` | Prompt files |
| `../schemas` | `/schemas` | JSON schemas |
| `../scripts` | `/repo/scripts` | Python scripts |
| `../requirements.txt` | `/repo/requirements.txt` | Python deps |

### nanoclaw volumes:
| Host (repo) | Container path | Purpose |
|---|---|---|
| `../nanoclaw/groups` | `/app/groups` | Agent config (read-only) |

---

## Environment Variables Passed to Containers

All sourced from `.env` (never commit `.env`).

### n8n receives:
```
N8N_BASIC_AUTH_USER, N8N_BASIC_AUTH_PASSWORD
GENERIC_TIMEZONE=America/New_York
N8N_WEBHOOK_TOKEN
GOOGLE_AI_API_KEY, IMAGEN_MODEL
GHL_API_KEY, GHL_LOCATION_ID, GHL_API_BASE
```

### nanoclaw receives:
```
OPENAI_API_KEY        ← primary AI key (OpenAI — not Anthropic)
DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID
N8N_BASE_URL=http://n8n:5678   ← internal Docker network address
N8N_WEBHOOK_TOKEN
NANOCLAW_GROUP
```

> **Important:** n8n and nanoclaw communicate over the internal Docker network.
> nanoclaw hits n8n at `http://n8n:5678` (service name), NOT `http://localhost:5678`.

---

## Common Commands

```bash
# Start the full stack (from repo root)
cd docker && docker compose up -d

# Stop the stack
cd docker && docker compose down

# View logs
docker logs nycpolicyscope-n8n -f
docker logs nycpolicyscope-nanoclaw -f

# Restart a single service
docker compose restart nanoclaw
docker compose restart n8n

# Rebuild nanoclaw (after code changes)
docker compose build nanoclaw && docker compose up -d nanoclaw

# Shell into n8n container
docker exec -it nycpolicyscope-n8n sh

# Shell into nanoclaw container
docker exec -it nycpolicyscope-nanoclaw sh

# Check n8n data volume
docker volume inspect nycpolicyscope-email-agent_n8n_data
```

---

## Full First-Time Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd Nycpolicyscope-email-agent

# 2. Setup nanoclaw source
bash scripts/setup_nanoclaw.sh

# 3. Configure environment
cp .env.example .env
# Edit .env: fill in OPENAI_API_KEY, DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID,
#            N8N_WEBHOOK_TOKEN, GOOGLE_AI_API_KEY, GHL_API_KEY, GHL_LOCATION_ID

# 4. Install Python deps (for local script testing)
pip install -r requirements.txt

# 5. Start Docker stack
cd docker && docker compose up -d

# 6. Import n8n workflows
# Open http://localhost:5678 → Settings → Import workflows
# Import all files from n8n/workflows/

# 7. Test the render pipeline
python scripts/validate_json.py data/sample/newsletter_content.json
python scripts/render_newsletter.py
```

---

## Deploying n8n to a VPS

For production deployment (DigitalOcean, Linode, etc.):

1. **Copy files to VPS:**
   ```bash
   rsync -avz --exclude='.env' --exclude='data/output/' . user@vps:/opt/nycpolicyscope/
   ```

2. **Set env vars on VPS:**
   ```bash
   cp .env.example .env && nano .env  # fill in production values
   ```

3. **Change webhook URL** in `.env`:
   ```
   N8N_BASE_URL=https://n8n.yourdomain.com
   ```

4. **Add nginx reverse proxy** for n8n (port 5678 → 443 with SSL)

5. **Run the stack:**
   ```bash
   cd docker && docker compose up -d
   ```

6. **Set up weekly cron** via n8n Schedule Trigger node (Phase 5)

---

## GitHub Actions (Phase 5 — Weekly Automation)

When ready to automate weekly newsletter generation, create `.github/workflows/weekly.yml`:

```yaml
name: Weekly Newsletter
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9am UTC
  workflow_dispatch:       # Manual trigger

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger n8n newsletter pipeline
        run: |
          curl -X POST ${{ secrets.N8N_BASE_URL }}/webhook/newsletter-pipeline \
            -H "X-Webhook-Token: ${{ secrets.N8N_WEBHOOK_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"content_file": "data/sample/newsletter_content.json"}'
```

Store `N8N_BASE_URL` and `N8N_WEBHOOK_TOKEN` as GitHub Secrets (not env vars).

---

## What NOT to do

- Do not commit `.env` to git — it contains API keys
- Do not expose n8n port 5678 directly to the internet without auth
- Do not store API keys in docker-compose.yml — always use `.env` references
- Do not delete `n8n_data` volume without backing up workflows first
- Do not change `http://n8n:5678` to `http://localhost:5678` for nanoclaw —
  they communicate over Docker network, not host network
