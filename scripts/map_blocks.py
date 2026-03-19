#!/usr/bin/env python3
"""
map_blocks.py — Template section mapping layer.

Converts a newsletter_blocks.json structure (meta + blocks[]) into
a Jinja2 template context dict. Handles two output modes:

  block_context  — passes blocks list directly; used by the block-aware
                   template path in newsletter.html
  flat_context   — maps blocks to legacy flat vars for backward compat

This module is imported by render_newsletter.py. It can also be run
directly as a CLI tool to inspect the mapped context.

Usage (as CLI):
    python scripts/map_blocks.py data/sample/newsletter_blocks.json
    python scripts/map_blocks.py data/sample/newsletter_blocks.json --mode flat
"""

import argparse
import json
import sys
from pathlib import Path


def to_block_context(blocks_data: dict) -> dict:
    """
    Returns a Jinja2 context dict where 'blocks' is the full ordered
    block list. The template iterates over blocks and renders each by type.

    This is the preferred mode for new block-aware templates.
    """
    meta = blocks_data["meta"]
    return {
        "subject_line": meta["subject_line"],
        "preview_text": meta["preview_text"],
        "edition": meta.get("edition", ""),
        "week_of": meta.get("week_of", ""),
        "blocks": blocks_data["blocks"],
    }


def to_flat_context(blocks_data: dict) -> dict:
    """
    Maps block-format data to the legacy flat context vars expected by
    the original newsletter.html template.

    Mapping rules:
      news_item blocks  → nyc_updates list
      first insight     → main_insight
      first feature     → feature_title + feature_body
      first tips        → quick_tips list
      first cta         → cta_text

    Multiple insight/feature/cta blocks beyond the first are silently
    dropped — this flat format does not support them. Use block_context
    for full multi-block rendering.
    """
    meta = blocks_data["meta"]
    flat = {
        "subject_line": meta["subject_line"],
        "preview_text": meta["preview_text"],
        "nyc_updates": [],
        "main_insight": "",
        "feature_title": "",
        "feature_body": "",
        "quick_tips": [],
        "cta_text": "",
    }

    insight_seen = False
    feature_seen = False
    tips_seen = False
    cta_seen = False

    for block in blocks_data["blocks"]:
        t = block["type"]
        if t == "news_item":
            flat["nyc_updates"].append({
                "borough": block["borough"],
                "body": block["body"],
            })
        elif t == "insight" and not insight_seen:
            flat["main_insight"] = block["body"]
            insight_seen = True
        elif t == "feature" and not feature_seen:
            flat["feature_title"] = block["title"]
            flat["feature_body"] = block["body"]
            feature_seen = True
        elif t == "tips" and not tips_seen:
            flat["quick_tips"] = block["items"]
            tips_seen = True
        elif t == "cta" and not cta_seen:
            flat["cta_text"] = block["body"]
            cta_seen = True
        # hero, links, event blocks are not mapped in flat mode

    return flat


def load_blocks(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Map newsletter_blocks.json to a Jinja2 template context and print it."
    )
    parser.add_argument("blocks_file", help="Path to newsletter_blocks.json")
    parser.add_argument(
        "--mode",
        choices=["block", "flat"],
        default="block",
        help="Context mode: 'block' (default) passes blocks list; 'flat' maps to legacy vars.",
    )
    args = parser.parse_args()

    path = Path(args.blocks_file)
    if not path.is_absolute():
        path = Path(__file__).parent.parent / path

    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    blocks_data = load_blocks(path)

    if args.mode == "flat":
        context = to_flat_context(blocks_data)
    else:
        context = to_block_context(blocks_data)

    print(json.dumps(context, indent=2))


if __name__ == "__main__":
    main()
