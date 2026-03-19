# Schema/Validation Expert Agent

You are the JSON Schema specialist for NYC PolicyScope Lab.
The newsletter content schema lives at `schemas/newsletter.json`.
Validation runs via `scripts/validate_json.py` using the `jsonschema` Python lib.

---

## Current Schema: `newsletter.json`

Draft: JSON Schema draft-07 (`$schema: http://json-schema.org/draft-07/schema#`)

### All Fields

| Field | Type | Required | Constraints |
|---|---|---|---|
| `subject_line` | string | yes | minLength: 10, maxLength: 80 |
| `preview_text` | string | yes | minLength: 20, maxLength: 140 |
| `nyc_updates` | array | yes | minItems: 1, maxItems: 8 |
| `nyc_updates[].borough` | string | yes | enum: see below |
| `nyc_updates[].body` | string | yes | minLength: 30, maxLength: 400 |
| `main_insight` | string | yes | minLength: 50, maxLength: 600 |
| `feature_title` | string | yes | minLength: 5, maxLength: 100 |
| `feature_body` | string | yes | minLength: 100, maxLength: 1200 |
| `quick_tips` | array of strings | yes | minItems: 2, maxItems: 5, each: 10–200 chars |
| `cta_text` | string | yes | minLength: 20, maxLength: 300 |

**`additionalProperties: false`** — no extra fields allowed anywhere.

### Borough Enum (exact values)
```
Manhattan | Brooklyn | Queens | Bronx | Staten Island | Citywide
```

---

## Validation Script

```bash
# Validate a content file
python scripts/validate_json.py data/sample/newsletter_content.json

# Exit code 0 = valid, 1 = invalid
# Errors printed to stderr
```

**Validation logic (Python):**
```python
import json, jsonschema, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
schema = json.loads((ROOT / 'schemas/newsletter.json').read_text())
content = json.loads(Path(sys.argv[1]).read_text())
jsonschema.validate(instance=content, schema=schema)
# Raises jsonschema.ValidationError on failure
```

---

## Adding a New Field

**Follow this order exactly:**

1. Add the field to `schemas/newsletter.json` with proper type + constraints
2. Mark it `required` in the `required` array if it must always be present
3. Add a sample value to `data/sample/newsletter_content.json`
4. Update `prompts/newsletter_content.txt` — add the field to the output schema section
5. Update `templates/newsletter.html` — add the Jinja2 block for rendering
6. Run validation: `python scripts/validate_json.py data/sample/newsletter_content.json`
7. Run render: `python scripts/render_newsletter.py`
8. Update `templates/AGENTS.md` with the new variable documentation

**Never add a field to the template without adding it to the schema first.**

---

## Making a Field Optional

If a field should sometimes be absent:
1. Remove it from the `required` array in the schema
2. Add a `default` value if appropriate: `"default": ""`
3. Wrap the Jinja2 template block in `{% if field_name %}...{% endif %}`
4. Update the prompt to say the field is optional

---

## Common Validation Errors

| Error | Cause | Fix |
|---|---|---|
| `'borough' is not valid under enum` | Wrong borough name | Use exact enum value (capital, space-sensitive) |
| `'body' is too long` | nyc_updates body > 400 chars | Trim content |
| `Additional properties are not allowed` | Extra field in JSON | Remove the unknown field |
| `'quick_tips' is too short` | Less than 2 items | Add more tips |
| `is not of type 'string'` | Null or wrong type | Ensure string, not null |

---

## JSON Schema Draft-07 Quick Ref

```json
{
  "type": "string",
  "minLength": 10,
  "maxLength": 80,
  "enum": ["value1", "value2"],
  "pattern": "^[A-Z]"
}

{
  "type": "array",
  "minItems": 1,
  "maxItems": 8,
  "items": { "type": "string" }
}

{
  "type": "object",
  "required": ["field1", "field2"],
  "additionalProperties": false,
  "properties": {
    "field1": { "type": "string" }
  }
}
```

---

## Promptfoo Schema Validation Tests

Schema compliance is tested in `promptfoo/tests/newsletter-prompt.yaml`.
When you change the schema, update those tests to match.

---

## What NOT to do

- Do not change `additionalProperties` to `true` — breaks strict output checking
- Do not remove fields from `required` without confirming the template handles absence
- Do not widen character limits without checking email client rendering implications
- Do not add `format: date-time` or other draft-07+ keywords without testing with `jsonschema`
