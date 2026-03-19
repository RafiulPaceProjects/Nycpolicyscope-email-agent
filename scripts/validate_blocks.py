#!/usr/bin/env python3
"""
validate_blocks.py — Block schema validator.

Validates a newsletter_blocks.json file against schemas/blocks.json.
Exits 0 on success, 1 on failure. Used by n8n workflows and CI.

Usage:
    python scripts/validate_blocks.py data/sample/newsletter_blocks.json
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema is required. Run: pip install jsonschema")
    sys.exit(1)


REPO_ROOT = Path(__file__).parent.parent
BLOCKS_SCHEMA_PATH = REPO_ROOT / "schemas" / "blocks.json"


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_blocks(blocks_data: dict, schema: dict) -> list:
    """
    Validate blocks_data against the blocks schema.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(blocks_data), key=lambda e: list(e.absolute_path)):
        path = " -> ".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  [{path}] {error.message}")
    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_blocks.py <path-to-blocks.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_absolute():
        input_path = REPO_ROOT / input_path

    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    if not BLOCKS_SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found: {BLOCKS_SCHEMA_PATH}")
        sys.exit(1)

    # Load files
    try:
        blocks_data = load_json(input_path)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {input_path}: {e}")
        sys.exit(1)

    schema = load_json(BLOCKS_SCHEMA_PATH)

    # Validate
    errors = validate_blocks(blocks_data, schema)

    if errors:
        print(f"INVALID: {input_path}")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        block_count = len(blocks_data.get("blocks", []))
        block_types = [b.get("type", "unknown") for b in blocks_data.get("blocks", [])]
        print(f"VALID: {input_path}")
        print(f"  {block_count} blocks: {', '.join(block_types)}")
        sys.exit(0)


if __name__ == "__main__":
    main()
