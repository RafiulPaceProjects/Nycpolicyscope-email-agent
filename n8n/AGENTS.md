# n8n Expert Agent

You are a deep specialist in **n8n** for the NYC PolicyScope newsletter pipeline.
All workflows live in `n8n/workflows/`. Study them before making any changes.

---

## The 4 Workflows

### 1. `newsletter_mvp.json` — Phase 1 Manual Pipeline
- **Trigger:** Manual (click in n8n UI)
- **What it does:** Reads sample JSON → parses → basic field check → renders HTML
- **Node chain:** ManualTrigger → ReadBinaryFile → Function (parse) → ReadBinaryFile → Function (validate fields) → ExecuteCommand (render_newsletter.py) → Function (log)
- **Key detail:** Uses `readBinaryFile` nodes — Phase 2 replaces these with HTTP Request nodes
- **Output:** HTML file in `data/output/`

### 2. `full_pipeline.json` — Webhook Full Pipeline
- **Trigger:** `POST /webhook/newsletter-pipeline`
- **Auth:** Header `X-Webhook-Token: <N8N_WEBHOOK_TOKEN>`
- **Body:** `{ "content_file": "data/sample/newsletter_content.json", "generate_images": true, "image_prompt": "..." }`
- **Node chain:** Webhook → SetParams → ExecuteCommand (validate_json.py) → CheckResult → ExecuteCommand (generate_image.py) → ParseImageResult → ExecuteCommand (render_newsletter.py) → ParseRenderResult
- **Output JSON:** `{ status, timestamp, content_file, html_preview, image_path, message }`
- **Shell injection guard:** `image_prompt` is sanitized — strips `` ` $ ( ) ; | & < > \ ``

### 3. `ghl_fetch_template.json` — Fetch GHL Email Templates
- **Trigger:** `POST /webhook/ghl-fetch-template`
- **Auth:** Header `X-Webhook-Token: <N8N_WEBHOOK_TOKEN>` (validated in first Function node)
- **What it does:** GETs email templates from GHL API → extracts id/name/type/subject/html → saves to `data/output/ghl_templates.json`
- **Requires:** `GHL_API_KEY`, `GHL_LOCATION_ID`, `GHL_API_BASE` in env
- **Phase 1 note:** Workflow structure complete but needs real GHL keys to activate

### 4. `generate_images.json` — Imagen 2 Image Generation
- **Trigger:** `POST /webhook/generate-images`
- **Body:** `{ "prompt": "...", "aspect_ratio": "16:9", "count": 1 }`
- **Valid ratios:** `1:1`, `16:9`, `9:16`, `4:3`, `3:4`
- **Max count:** 4
- **Shell injection guard:** Prompt sanitized before injecting into ExecuteCommand
- **Output:** `{ status: 'success', prompt, aspect_ratio, images: [path, ...] }`
- **Requires:** `GOOGLE_AI_API_KEY` in n8n container env

---

## Node Types Used in This Project

| Node | Purpose |
|---|---|
| `n8n-nodes-base.webhook` | HTTP webhook trigger with path/method/auth |
| `n8n-nodes-base.manualTrigger` | Click-to-run in n8n UI |
| `n8n-nodes-base.function` | JavaScript business logic (items[]/`$input`) |
| `n8n-nodes-base.executeCommand` | Run shell commands (Python scripts) |
| `n8n-nodes-base.readBinaryFile` | Read files from mounted volume |
| `n8n-nodes-base.writeBinaryFile` | Write files to mounted volume |
| `n8n-nodes-base.httpRequest` | External API calls (GHL, news APIs) |
| `n8n-nodes-base.respondToWebhook` | Send response back to webhook caller |

---

## How Python Scripts Are Called from n8n

All ExecuteCommand nodes follow this pattern:
```
cd /repo && python scripts/<script>.py [args]
```

**Volume mappings (docker-compose.yml):**
- `../scripts` → `/repo/scripts` inside n8n container
- `../data` → `/data` inside n8n container
- `../templates` → `/templates`
- `../schemas` → `/schemas`
- `../prompts` → `/prompts`

So `/repo/scripts/render_newsletter.py` inside n8n = `scripts/render_newsletter.py` in your repo.

---

## Webhook Authentication Pattern

All production webhooks use token auth:
```javascript
// In the validate node:
const token = $input.first().headers['x-webhook-token'];
const expected = process.env.N8N_WEBHOOK_TOKEN || '';
if (token !== expected) throw new Error('Unauthorized');
```

nanoclaw sends: `headers: { 'X-Webhook-Token': process.env.N8N_WEBHOOK_TOKEN }`

---

## Accessing Previous Node Data in Function Nodes

```javascript
// Get output from a specific node by name:
const params = $node['Set Pipeline Parameters'].json;

// Get current input:
const data = $input.first().json;

// Get all items:
const items = $input.all();
```

---

## Adding a New Workflow

1. Create `n8n/workflows/<name>.json` using the existing files as templates
2. Required top-level fields: `name`, `description`, `nodes`, `connections`, `active`, `version`, `tags`
3. Each node needs: `id`, `name`, `type`, `position`, `parameters`
4. Import into n8n UI: Settings → Import workflow → paste JSON
5. Add the webhook path to `nanoclaw/groups/nycpolicyscope/CLAUDE.md` if nanoclaw will trigger it
6. Document in root `AGENTS.md` file table

---

## Common n8n Bugs / Gotchas

- **Binary data reads:** `items[0].binary.data.data` is base64 — always `Buffer.from(raw, 'base64').toString('utf-8')` before JSON.parse
- **Expression syntax:** In node parameters use `={{ expression }}` not `{{ expression }}`
- **ExecuteCommand exitCode:** Always check `result.exitCode !== 0` before assuming success
- **Webhook not receiving:** Check that `active: true` in the JSON and the workflow is activated in n8n UI
- **Volume file paths:** Use `/data/`, `/templates/` etc. (container paths), not repo-relative paths inside ExecuteCommand
- **Env vars in Function nodes:** Access with `process.env.VAR_NAME`
- **Env vars in HTTP Request nodes:** Access with `$env.VAR_NAME` in expressions

---

## Phase 2 Upgrade Path

When adding live news API ingestion:
1. Replace `n8n-nodes-base.readBinaryFile` nodes with `n8n-nodes-base.httpRequest`
2. Add an OpenAI node (or ExecuteCommand calling an OpenAI Python script) to generate content from raw updates
3. Validate generated content through `validate_json.py` before rendering
4. Store generated content to `data/sample/newsletter_content.json` as a checkpoint

---

## n8n Admin

- **UI:** http://localhost:5678
- **Basic auth:** `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD`
- **Workflow import:** Settings → Import from file / JSON
- **Execution history:** Left sidebar → Executions
- **Credential management:** Left sidebar → Credentials
