#!/usr/bin/env python3
"""
generate_snippets.py — AI snippet generator.

Reads raw_news.json (or nyc_updates.json), calls OpenAI to generate
structured newsletter blocks, validates the output against schemas/blocks.json,
and writes newsletter_blocks.json to the output path.

This is the pipeline step that replaces manual JSON authoring.

Usage:
    python scripts/generate_snippets.py
    python scripts/generate_snippets.py --input data/sample/nyc_updates.json
    python scripts/generate_snippets.py --input data/sample/nyc_updates.json --output data/output/blocks.json
    python scripts/generate_snippets.py --dry-run   # prints prompt without calling OpenAI

Dependencies:
    pip install openai python-dotenv jsonschema
    Set OPENAI_API_KEY in .env

Pipeline position:
    nyc_updates.json → generate_snippets.py → newsletter_blocks.json → render_newsletter.py
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv is required. Run: pip install python-dotenv")
    sys.exit(1)

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema is required. Run: pip install jsonschema")
    sys.exit(1)

try:
    import openai
except ImportError:
    print("ERROR: openai is required. Run: pip install openai")
    sys.exit(1)


REPO_ROOT = Path(__file__).parent.parent
DEFAULT_INPUT = REPO_ROOT / "data" / "sample" / "nyc_updates.json"
DEFAULT_PROMPT_TEMPLATE = REPO_ROOT / "prompts" / "snippet_generation.txt"
BLOCKS_SCHEMA_PATH = REPO_ROOT / "schemas" / "blocks.json"
OUTPUT_DIR = REPO_ROOT / "data" / "output"

load_dotenv(REPO_ROOT / ".env")


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(raw_news: dict, prompt_template: str) -> str:
    """Interpolate the raw news JSON into the prompt template."""
    updates_json = json.dumps(raw_news, indent=2)
    return prompt_template.replace("{{ updates }}", updates_json)


def call_openai(prompt: str) -> str:
    """
    Call OpenAI gpt-4o with the prompt and return the raw response string.
    Uses response_format=json_object to enforce JSON-only output.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("  Set it in .env or export it in your shell.")
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a structured content generator for NYC PolicyScope, "
                    "a weekly NYC policy newsletter. You produce JSON only. "
                    "Follow the schema instructions exactly."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content


def validate_blocks(blocks_data: dict, schema: dict) -> list:
    """Returns list of error messages. Empty means valid."""
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(blocks_data), key=lambda e: list(e.absolute_path)):
        path = " -> ".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  [{path}] {error.message}")
    return errors


def save_output(blocks_data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(blocks_data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured newsletter blocks from raw NYC news via OpenAI."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to raw news JSON (default: data/sample/nyc_updates.json)",
    )
    parser.add_argument(
        "--prompt",
        default=str(DEFAULT_PROMPT_TEMPLATE),
        help="Path to prompt template (default: prompts/snippet_generation.txt)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for newsletter_blocks.json (default: data/output/blocks_YYYYMMDD_HHMMSS.json)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip schema validation of the generated blocks",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the assembled prompt without calling OpenAI",
    )
    args = parser.parse_args()

    # Resolve paths
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = REPO_ROOT / input_path

    prompt_path = Path(args.prompt)
    if not prompt_path.is_absolute():
        prompt_path = REPO_ROOT / prompt_path

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = REPO_ROOT / output_path
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"blocks_{timestamp}.json"

    # Load inputs
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)
    if not prompt_path.exists():
        print(f"ERROR: Prompt template not found: {prompt_path}")
        sys.exit(1)

    print(f"Loading raw news: {input_path}")
    raw_news = load_json(input_path)

    print(f"Loading prompt template: {prompt_path}")
    prompt_template = load_text(prompt_path)
    prompt = build_prompt(raw_news, prompt_template)

    if args.dry_run:
        print("\n--- ASSEMBLED PROMPT (dry run) ---\n")
        print(prompt)
        print("\n--- END PROMPT ---")
        print("\nDry run complete. No OpenAI call made.")
        sys.exit(0)

    # Call OpenAI
    print("Calling OpenAI gpt-4o...")
    raw_response = call_openai(prompt)

    # Parse response
    try:
        blocks_data = json.loads(raw_response)
    except json.JSONDecodeError as e:
        print(f"ERROR: OpenAI returned non-JSON response: {e}")
        print(f"Raw response:\n{raw_response[:500]}")
        sys.exit(1)

    # Validate
    if not args.no_validate:
        if not BLOCKS_SCHEMA_PATH.exists():
            print(f"WARNING: Schema not found at {BLOCKS_SCHEMA_PATH} — skipping validation.")
        else:
            print(f"Validating against schema: {BLOCKS_SCHEMA_PATH}")
            schema = load_json(BLOCKS_SCHEMA_PATH)
            errors = validate_blocks(blocks_data, schema)
            if errors:
                print("  ERROR: Generated blocks failed schema validation:")
                for err in errors:
                    print(err)
                print("\nRaw generated JSON:")
                print(json.dumps(blocks_data, indent=2)[:1000])
                sys.exit(1)
            block_count = len(blocks_data.get("blocks", []))
            print(f"  Validation passed. {block_count} blocks generated.")
    else:
        print("Skipping schema validation (--no-validate).")

    # Save
    save_output(blocks_data, output_path)
    print(f"Blocks saved: {output_path}")
    print()
    print("Success. Next step: render with render_newsletter.py")
    print(f"  python scripts/render_newsletter.py --content {output_path}")


if __name__ == "__main__":
    main()
