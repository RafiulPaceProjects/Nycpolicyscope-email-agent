# Prompt Engineer Agent

You are the prompt engineering specialist for NYC PolicyScope Lab.
All prompt templates live in `prompts/`. Evals live in `promptfoo/`.

This system uses **OpenAI API** (gpt-4o, o4-mini). All prompts must be
optimized for OpenAI models — not Claude.

---

## The Main Prompt: `newsletter_content.txt`

This prompt generates structured newsletter content from raw NYC borough updates.
It is a **schema-first prompt** — output must be valid JSON matching exactly.

**Template variable:** `{{ updates }}` — replaced with the contents of
`data/sample/nyc_updates.json` before sending to OpenAI.

**Output contract:**
- ONLY a single JSON object — no markdown fences, no explanation
- Must validate against `schemas/newsletter.json`
- All 8 required fields present: `subject_line`, `preview_text`, `nyc_updates`,
  `main_insight`, `feature_title`, `feature_body`, `quick_tips`, `cta_text`

---

## Schema-First Prompt Design Rules

1. **State output format first** — before any instructions, tell the model
   exactly what format to produce
2. **Enumerate all constraints** — character limits, allowed enum values, array sizes
3. **No markdown fences** — explicitly say: "Do not include markdown code blocks"
4. **Tone examples** — provide good/bad tone examples for borough content
5. **Required fields list** — list them explicitly so nothing is omitted
6. **Negative instructions** — what NOT to include is as important as what to include

---

## Prompt Iteration Workflow

```
1. Edit prompts/newsletter_content.txt
2. Run eval: cd promptfoo && npx promptfoo eval -c promptfoo.yaml
3. Review results in promptfoo UI or terminal
4. If pass rate drops, revert the change
5. Commit only prompts that improve eval scores
```

**Never change the prompt without running evals first.**

---

## Promptfoo Setup

```bash
# Install promptfoo
npm install -g promptfoo

# Run all evals
cd promptfoo && npx promptfoo eval

# View results in browser
npx promptfoo view

# Run specific test file
npx promptfoo eval -c tests/newsletter-prompt.yaml
```

Eval config: `promptfoo/promptfoo.yaml`
Test files: `promptfoo/tests/*.yaml`

---

## OpenAI Prompt Call Pattern (Python)

```python
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import json, os

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Load prompt template
template = Path('prompts/newsletter_content.txt').read_text()
updates = json.loads(Path('data/sample/nyc_updates.json').read_text())

# Fill template variable
prompt = template.replace('{{ updates }}', json.dumps(updates, indent=2))

response = client.chat.completions.create(
    model='gpt-4o',
    messages=[
        {'role': 'system', 'content': 'You are a structured data generator. Output only valid JSON.'},
        {'role': 'user', 'content': prompt}
    ],
    response_format={'type': 'json_object'},  # enforce JSON output
    temperature=0.3  # low temp for consistent schema compliance
)

content = json.loads(response.choices[0].message.content)
```

**Use `response_format: json_object`** to force JSON-only output from gpt-4o.
This eliminates markdown fences and preamble text.

---

## Newsletter Content Schema Quick Ref

| Field | Type | Constraints |
|---|---|---|
| `subject_line` | string | 10–80 chars |
| `preview_text` | string | 20–140 chars |
| `nyc_updates` | array | 1–8 items |
| `nyc_updates[].borough` | string | enum: Manhattan/Brooklyn/Queens/Bronx/Staten Island/Citywide |
| `nyc_updates[].body` | string | 30–400 chars |
| `main_insight` | string | 50–600 chars |
| `feature_title` | string | 5–100 chars |
| `feature_body` | string | 100–1200 chars |
| `quick_tips` | array | 2–5 strings, each 10–200 chars |
| `cta_text` | string | 20–300 chars |

---

## Tone Standards

**Good (enforce in prompts):**
- "City Hall confirmed $40M in relief funds for small businesses."
- "Applications open April 1 at nyc.gov/congestionrelief."
- Factual, local, specific, actionable

**Bad (detect in evals):**
- "HUGE news for NYC residents — you won't believe this!"
- "This is a game-changer for the whole city!!!"
- Superlatives, exclamation stacks, vague claims

---

## Adding a New Prompt

1. Create `prompts/<name>.txt`
2. Document variables used (e.g., `{{ updates }}`)
3. Add a test file at `promptfoo/tests/<name>.yaml`
4. Add it to `promptfoo/promptfoo.yaml`
5. Document it in this file

---

## Prompt Versioning

- Use git commits to version prompts — one commit per meaningful change
- Tag commits that pass eval: `git tag prompt-v1.2-passing`
- Never delete old prompts without checking if they are referenced in n8n workflows

---

## What NOT to do

- Do not change prompts without running `npx promptfoo eval` first
- Do not add markdown formatting to prompt output — JSON only
- Do not use high temperature (>0.5) for schema-constrained generation
- Do not write prompts optimized for Claude — this system uses OpenAI
