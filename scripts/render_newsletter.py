#!/usr/bin/env python3
"""
render_newsletter.py

Reads a newsletter content JSON, validates it against the appropriate schema,
maps the content to a Jinja2 template context, renders the HTML, and saves
a preview file to data/output/.

Supports two content formats automatically detected by file structure:

  FLAT format (legacy, newsletter_content.json):
    { "subject_line": "...", "nyc_updates": [...], ... }
    Validated against schemas/newsletter.json
    Rendered using flat template vars

  BLOCK format (new, newsletter_blocks.json):
    { "meta": { "subject_line": "..." }, "blocks": [...] }
    Validated against schemas/blocks.json
    Rendered using block-aware template vars (blocks list passed to template)

The same newsletter.html template handles both formats via a Jinja2 conditional.

Usage:
    python scripts/render_newsletter.py
    python scripts/render_newsletter.py --content data/sample/newsletter_blocks.json
    python scripts/render_newsletter.py --content data/sample/newsletter_content.json
    python scripts/render_newsletter.py --content path/to/blocks.json --output data/output/preview.html
    python scripts/render_newsletter.py --format flat    # force flat mode
    python scripts/render_newsletter.py --format blocks  # force block mode

Dependencies:
    pip install jinja2 jsonschema
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("ERROR: jinja2 is required. Run: pip install jinja2 jsonschema")
    sys.exit(1)

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema is required. Run: pip install jinja2 jsonschema")
    sys.exit(1)

# Import the mapping layer
sys.path.insert(0, str(Path(__file__).parent))
try:
    from map_blocks import to_block_context, to_flat_context
except ImportError:
    print("ERROR: map_blocks.py not found in scripts/. This file is required.")
    sys.exit(1)


# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = REPO_ROOT / "templates"
SCHEMA_FLAT = REPO_ROOT / "schemas" / "newsletter.json"
SCHEMA_BLOCKS = REPO_ROOT / "schemas" / "blocks.json"
DEFAULT_CONTENT = REPO_ROOT / "data" / "sample" / "newsletter_content.json"
OUTPUT_DIR = REPO_ROOT / "data" / "output"


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_format(content: dict) -> str:
    """
    Auto-detect whether a content file is flat (legacy) or block format.
    Block format has 'meta' and 'blocks' keys at the root.
    Flat format has 'subject_line' at the root.
    """
    if "meta" in content and "blocks" in content:
        return "blocks"
    if "subject_line" in content:
        return "flat"
    return "unknown"


def validate_content(content: dict, schema: dict) -> None:
    """Validate content against schema. Raises jsonschema.ValidationError on failure."""
    jsonschema.validate(instance=content, schema=schema)


def validate_all_errors(content: dict, schema: dict) -> list:
    """Returns all validation error messages for reporting. Empty list = valid."""
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(content), key=lambda e: list(e.absolute_path)):
        path = " -> ".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  [{path}] {error.message}")
    return errors


def build_template_context(content: dict, fmt: str) -> dict:
    """
    Build the Jinja2 context from content based on format.

    Flat format: content dict is used directly as template vars.
    Block format: map_blocks.to_block_context() converts to { subject_line, preview_text, blocks[] }
    """
    if fmt == "blocks":
        return to_block_context(content)
    # flat: pass content directly
    return content


def render_html(context: dict, template_name: str = "newsletter.html") -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(template_name)
    return template.render(**context)


def save_output(html: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    parser = argparse.ArgumentParser(
        description="Render NYC PolicyScope newsletter HTML preview. Supports flat and block content formats."
    )
    parser.add_argument(
        "--content",
        default=str(DEFAULT_CONTENT),
        help="Path to newsletter content JSON. Flat (newsletter_content.json) or block (newsletter_blocks.json) format. Default: data/sample/newsletter_content.json",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output HTML file path (default: data/output/newsletter_YYYYMMDD_HHMMSS.html)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip JSON schema validation",
    )
    parser.add_argument(
        "--format",
        choices=["flat", "blocks", "auto"],
        default="auto",
        help="Content format: 'flat' (legacy), 'blocks' (new), or 'auto' to detect. Default: auto",
    )
    args = parser.parse_args()

    # Resolve paths
    content_path = Path(args.content)
    if not content_path.is_absolute():
        content_path = REPO_ROOT / content_path

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = REPO_ROOT / output_path
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"newsletter_{timestamp}.html"

    # Load content
    print(f"Loading content: {content_path}")
    if not content_path.exists():
        print(f"ERROR: Content file not found: {content_path}")
        sys.exit(1)

    content = load_json(content_path)

    # Detect format
    if args.format == "auto":
        fmt = detect_format(content)
        if fmt == "unknown":
            print("ERROR: Could not detect content format.")
            print("  Expected either { 'subject_line': ... } (flat) or { 'meta': ..., 'blocks': [...] } (blocks).")
            sys.exit(1)
        print(f"Detected format: {fmt}")
    else:
        fmt = args.format
        print(f"Using format: {fmt} (explicit)")

    # Validate
    if not args.no_validate:
        if fmt == "blocks":
            schema_path = SCHEMA_BLOCKS
        else:
            schema_path = SCHEMA_FLAT

        if not schema_path.exists():
            print(f"WARNING: Schema not found at {schema_path} — skipping validation.")
        else:
            print(f"Validating against schema: {schema_path}")
            schema = load_json(schema_path)
            errors = validate_all_errors(content, schema)
            if errors:
                print("  ERROR: Schema validation failed:")
                for err in errors:
                    print(err)
                sys.exit(1)
            print("  Validation passed.")
    else:
        print("Skipping schema validation (--no-validate).")

    # Build template context
    context = build_template_context(content, fmt)

    # Determine template name
    template_name = "newsletter.html"
    if fmt == "blocks" and "template" in content.get("meta", {}):
        # Allow meta.template to select a different template file in the future
        meta_template = content["meta"]["template"]
        candidate = f"{meta_template}.html"
        if (TEMPLATE_DIR / candidate).exists():
            template_name = candidate

    # Render
    print(f"Rendering template: {template_name}")
    html = render_html(context, template_name)

    # Save
    save_output(html, output_path)
    print(f"Preview saved: {output_path}")
    print()
    print("Success. Open the file in a browser to review the newsletter.")
    print(f"  file://{output_path.resolve()}")


if __name__ == "__main__":
    main()
