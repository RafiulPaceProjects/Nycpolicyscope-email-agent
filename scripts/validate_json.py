#!/usr/bin/env python3
"""
validate_json.py

Validates any JSON file against the newsletter schema.
Useful for checking AI-generated content before rendering.

Usage:
    python scripts/validate_json.py data/sample/newsletter_content.json
    python scripts/validate_json.py data/output/my_content.json
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema is required. Run: pip install jinja2 jsonschema")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "newsletter.json"


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path-to-content.json>")
        sys.exit(1)

    content_path = Path(sys.argv[1])
    if not content_path.is_absolute():
        content_path = REPO_ROOT / content_path

    if not content_path.exists():
        print(f"ERROR: File not found: {content_path}")
        sys.exit(1)

    with open(content_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=content, schema=schema)
        print(f"VALID: {content_path}")
        print(f"  All required fields present and within constraints.")
        sys.exit(0)
    except jsonschema.ValidationError as e:
        print(f"INVALID: {content_path}")
        print(f"  Error: {e.message}")
        print(f"  Path:  {' -> '.join(str(p) for p in e.absolute_path)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
