# Builder Agent — Python Scripts

You are the code-building specialist for NYC PolicyScope Lab scripts.
All scripts live in `scripts/`. They are called by n8n `ExecuteCommand` nodes
and can also be run directly from the terminal.

---

## The 4 Scripts

### `render_newsletter.py`
Renders the HTML newsletter from structured content JSON.

**Usage:**
```bash
python scripts/render_newsletter.py
python scripts/render_newsletter.py --content data/sample/newsletter_content.json
```

**What it does:**
1. Loads content JSON (default: `data/sample/newsletter_content.json`)
2. Validates against `schemas/newsletter.json` (using `jsonschema`)
3. Renders `templates/newsletter.html` (Jinja2)
4. Saves output to `data/output/newsletter_YYYYMMDD_HHMMSS.html`
5. Prints: `Preview saved: data/output/newsletter_YYYYMMDD_HHMMSS.html`
   (n8n parses this line to get the output path)

**n8n call:**
```
cd /repo && python scripts/render_newsletter.py --content {{ $json.content_file }}
```

**Key dependencies:** `jinja2`, `jsonschema`, `python-dotenv`, `pathlib`

---

### `validate_json.py`
Validates a JSON file against `schemas/newsletter.json`.

**Usage:**
```bash
python scripts/validate_json.py data/sample/newsletter_content.json
```

**Exit codes:**
- `0` = valid
- `1` = validation failed (error on stderr)

**n8n call:**
```
cd /repo && python scripts/validate_json.py {{ $json.content_file }}
```
n8n checks `exitCode !== 0` to detect failure.

---

### `generate_image.py`
Generates images using Google Imagen 2 via AI Studio API.

**Usage:**
```bash
python scripts/generate_image.py --prompt "NYC skyline" --ratio 16:9 --count 1 --json
```

**Arguments:**
- `--prompt` — image description (required)
- `--ratio` — aspect ratio: `1:1`, `16:9`, `9:16`, `4:3`, `3:4` (default: `16:9`)
- `--count` — number of images (1–4, default: 1)
- `--json` — output JSON instead of plain text

**JSON output format:**
```json
{
  "status": "success",
  "images": ["data/output/images/image_20260319_120000_0.png"],
  "prompt": "NYC skyline",
  "aspect_ratio": "16:9"
}
```

**Requires:** `GOOGLE_AI_API_KEY` in `.env`
**Model:** `IMAGEN_MODEL` env var (default: `imagen-3.0-generate-002`)
**Output dir:** `data/output/images/`

---

### `setup_nanoclaw.sh`
First-run shell script to clone the nanoclaw TypeScript source.
Run once before `docker compose up`. Idempotent — safe to re-run.

**Usage:**
```bash
bash scripts/setup_nanoclaw.sh
```

---

## Coding Patterns Used in This Project

### Arg parsing
```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--content', default='data/sample/newsletter_content.json')
args = parser.parse_args()
```

### Env loading
```python
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')  # OpenAI — not Anthropic
```

### File paths
```python
from pathlib import Path
ROOT = Path(__file__).parent.parent
content_path = ROOT / args.content
```

### JSON validation
```python
import jsonschema, json
schema = json.loads((ROOT / 'schemas/newsletter.json').read_text())
content = json.loads(content_path.read_text())
jsonschema.validate(instance=content, schema=schema)
```

### Jinja2 rendering
```python
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader(str(ROOT / 'templates')))
template = env.get_template('newsletter.html')
html = template.render(**content)
```

---

## Adding a New Script

1. Create `scripts/<name>.py`
2. Use `argparse` for CLI args, `dotenv` for env vars, `pathlib` for paths
3. Print machine-parseable output for n8n (e.g., `Preview saved: <path>`)
4. Exit with code `0` on success, `1` on failure (n8n checks this)
5. Add the n8n ExecuteCommand call pattern to `n8n/AGENTS.md`
6. Document the script in this file

---

## Running Scripts Locally

```bash
# From repo root
cd /home/user/Nycpolicyscope-email-agent

# Install deps
pip install -r requirements.txt

# Validate
python scripts/validate_json.py data/sample/newsletter_content.json

# Render
python scripts/render_newsletter.py

# Generate image (requires GOOGLE_AI_API_KEY in .env)
python scripts/generate_image.py --prompt "NYC city hall editorial photo" --ratio 16:9 --json
```

---

## requirements.txt

```
jinja2
jsonschema
python-dotenv
requests
openai
```

When adding a new dependency: add to `requirements.txt` AND rebuild the n8n
container if the script is called from n8n.

---

## n8n ExecuteCommand Notes

- Scripts run inside the n8n container as `cd /repo && python scripts/<name>.py`
- `/repo/scripts/` = `scripts/` in your repo (mounted volume)
- `/data/` = `data/` in your repo
- Env vars are passed from `docker-compose.yml` → available as `os.getenv()`
- Stdout and stderr are captured in `$json.stdout` / `$json.stderr`
- Exit code in `$json.exitCode`

---

## What NOT to do

- Do not hardcode file paths — always use `pathlib.Path` relative to `ROOT`
- Do not print debug noise to stdout — n8n parses stdout for specific patterns
- Do not use `sys.exit()` with non-standard codes — only `0` and `1`
- Do not write directly to stdout AND return JSON — use `--json` flag pattern
