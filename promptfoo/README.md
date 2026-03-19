# Promptfoo Eval Framework

Prompt evaluation for NYC PolicyScope Lab using [promptfoo](https://promptfoo.dev).

All evals run against **OpenAI** (gpt-4o / gpt-4o-mini).

---

## Setup

```bash
# Install promptfoo globally
npm install -g promptfoo

# Or use npx (no install needed)
npx promptfoo eval
```

Set your OpenAI API key in `.env` (project root):
```
OPENAI_API_KEY=sk-...
```

promptfoo reads `OPENAI_API_KEY` from the environment automatically.

---

## Running Evals

```bash
# From this directory (promptfoo/)
cd promptfoo

# Run all test suites
npx promptfoo eval

# Run specific test file
npx promptfoo eval -c promptfoo.yaml --filter-tests newsletter-prompt
npx promptfoo eval -c promptfoo.yaml --filter-tests nanoclaw-manager
npx promptfoo eval -c promptfoo.yaml --filter-tests nanoclaw-n8n-expert

# View results in browser
npx promptfoo view

# Output results to JSON
npx promptfoo eval --output results/latest.json
```

---

## Test Suites

| File | What It Tests |
|---|---|
| `tests/newsletter-prompt.yaml` | `prompts/newsletter_content.txt` — schema compliance, character limits, tone |
| `tests/nanoclaw-manager.yaml` | `nanoclaw/groups/nycpolicyscope/CLAUDE.md` — manager agent behavior |
| `tests/nanoclaw-n8n-expert.yaml` | `nanoclaw/groups/n8n-expert/CLAUDE.md` — n8n expert knowledge |

---

## What Gets Tested

### newsletter-prompt.yaml (8 tests)
- All 8 required fields are present in output
- `subject_line` is 10–80 characters
- `preview_text` is 20–140 characters
- All boroughs are valid enum values
- No hype words in `subject_line`
- All `nyc_updates.body` fields are 30–400 characters
- `quick_tips` has 2–5 items
- No markdown code fences in output (JSON only)

### nanoclaw-manager.yaml (6 tests)
- Detects missing required fields
- Flags body text over 400 characters
- Rejects invalid borough names
- Catches hype/clickbait tone
- Refuses template redesign requests
- Gives specific field-level feedback, not vague praise

### nanoclaw-n8n-expert.yaml (7 tests)
- Knows correct webhook paths
- Knows X-Webhook-Token auth pattern
- Diagnoses exitCode 1 failures (check stderr)
- Knows base64 binary decode pattern
- Knows `$node['Name'].json` syntax
- Knows generate-images request body format
- Redirects Python coding to builder agent

---

## Adding a New Test

1. Open the relevant `tests/*.yaml` file
2. Add a new test block under `tests:`:
   ```yaml
   - description: What this test checks
     vars:
       updates: |
         [your test input here]
     assert:
       - type: javascript
         value: |
           // return true to pass, string message to fail
           return output.includes('expected value');
         description: What the assertion checks
   ```
3. Run `npx promptfoo eval` to verify it works
4. Commit with a clear message describing the new eval coverage

---

## Adding a New Test Suite

1. Create `tests/<name>.yaml`
2. Add the file to `promptfoo.yaml` under `tests:`
3. Document it in this README

---

## Assertion Types Reference

| Type | Use case |
|---|---|
| `is-json` | Output must be valid JSON |
| `javascript` | Custom logic — return `true` or error string |
| `contains` | Output must contain a substring |
| `not-contains` | Output must NOT contain a substring |
| `regex` | Output must match a regex pattern |
| `llm-rubric` | Use an LLM to judge quality (slower, costs more) |

Full docs: https://promptfoo.dev/docs/configuration/assertions

---

## Workflow

1. Change a prompt or agent CLAUDE.md
2. Run `npx promptfoo eval`
3. If any test fails, fix the prompt
4. If all tests pass, commit the change
5. Tag good prompt versions: `git tag prompt-v1.x-passing`
