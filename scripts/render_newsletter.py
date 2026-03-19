#!/usr/bin/env python3
"""
render_newsletter.py

Reads structured newsletter content JSON, validates it against the schema,
renders the HTML template, and saves a preview file to data/output/.

Usage:
    python scripts/render_newsletter.py
    python scripts/render_newsletter.py --content data/sample/newsletter_content.json
    python scripts/render_newsletter.py --content data/sample/newsletter_content.json --output data/output/preview.html

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


# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = REPO_ROOT / "templates"
SCHEMA_PATH = REPO_ROOT / "schemas" / "newsletter.json"
DEFAULT_CONTENT = REPO_ROOT / "data" / "sample" / "newsletter_content.json"
OUTPUT_DIR = REPO_ROOT / "data" / "output"


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_content(content: dict, schema: dict) -> None:
    """Validate content against schema. Raises jsonschema.ValidationError on failure."""
    jsonschema.validate(instance=content, schema=schema)


def render_html(content: dict, template_name: str = "newsletter.html") -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(template_name)
    return template.render(**content)


def save_output(html: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    parser = argparse.ArgumentParser(description="Render NYC PolicyScope newsletter HTML preview.")
    parser.add_argument(
        "--content",
        default=str(DEFAULT_CONTENT),
        help="Path to structured newsletter content JSON (default: data/sample/newsletter_content.json)",
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

    # Validate
    if not args.no_validate:
        print(f"Validating against schema: {SCHEMA_PATH}")
        schema = load_json(SCHEMA_PATH)
        try:
            validate_content(content, schema)
            print("  Validation passed.")
        except jsonschema.ValidationError as e:
            print(f"  ERROR: Schema validation failed:\n  {e.message}")
            print(f"  Path: {' -> '.join(str(p) for p in e.absolute_path)}")
            sys.exit(1)
    else:
        print("Skipping schema validation (--no-validate).")

    # Render
    print("Rendering HTML template...")
    html = render_html(content)

    # Save
    save_output(html, output_path)
    print(f"Preview saved: {output_path}")
    print()
    print("Success. Open the file in a browser to review the newsletter.")
    print(f"  file://{output_path.resolve()}")


if __name__ == "__main__":
    main()
