#!/usr/bin/env python3
"""
generate_image.py

Generates images using Google Imagen 2 (via Google AI Studio API).
Returns raw PNG files saved to data/output/images/.

WHY NO LOGO:
  When using the Google AI Studio API directly, images are returned as raw
  base64-encoded PNG data — no Gemini branding, watermark overlay, or logo.
  The visible Gemini logo only appears in the web UI (gemini.google.com).
  SynthID (an invisible perceptual watermark) is embedded by Google at the
  pixel level and cannot be removed without degrading the image — this is
  separate from any visible branding.

Usage:
    python scripts/generate_image.py --prompt "NYC skyline at sunrise, editorial style"
    python scripts/generate_image.py --prompt "Brooklyn bridge aerial" --ratio 1:1
    python scripts/generate_image.py --prompt "City Hall close-up" --count 2

Dependencies:
    pip install google-generativeai python-dotenv

Environment variables required:
    GOOGLE_AI_API_KEY  — from https://aistudio.google.com/app/apikey
    IMAGEN_MODEL       — optional, defaults to imagen-3.0-generate-002
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — env vars can be set directly

try:
    import google.generativeai as genai
    from google.generativeai import types as genai_types
except ImportError:
    print("ERROR: google-generativeai is required.")
    print("Run: pip install google-generativeai python-dotenv")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "output" / "images"

VALID_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4"]
DEFAULT_MODEL = "imagen-3.0-generate-002"


def get_api_key() -> str:
    key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if not key:
        print("ERROR: GOOGLE_AI_API_KEY environment variable is not set.")
        print("  1. Get a key from https://aistudio.google.com/app/apikey")
        print("  2. Copy .env.example to .env and fill in GOOGLE_AI_API_KEY")
        sys.exit(1)
    return key


def generate_images(
    prompt: str,
    count: int = 1,
    aspect_ratio: str = "16:9",
    model: str = DEFAULT_MODEL,
) -> list[Path]:
    """
    Call Imagen 2 via Google AI Studio API.
    Returns list of saved PNG file paths.
    Images are raw PNG — no visible logo or watermark overlay.
    """
    api_key = get_api_key()
    model_name = os.environ.get("IMAGEN_MODEL", model)

    genai.configure(api_key=api_key)

    print(f"Model:        {model_name}")
    print(f"Prompt:       {prompt}")
    print(f"Aspect ratio: {aspect_ratio}")
    print(f"Count:        {count}")
    print("Generating...")

    response = genai.ImageGenerationModel(model_name).generate_images(
        prompt=prompt,
        number_of_images=count,
        aspect_ratio=aspect_ratio,
        # safety_filter_level="block_only_high",  # uncomment to relax filter
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, image in enumerate(response.images):
        filename = f"image_{timestamp}_{i+1}.png"
        output_path = OUTPUT_DIR / filename

        # image.image_bytes is raw PNG bytes — no logo
        with open(output_path, "wb") as f:
            f.write(image._image_bytes)

        saved_paths.append(output_path)
        print(f"  Saved: {output_path}")

    return saved_paths


def main():
    parser = argparse.ArgumentParser(
        description="Generate images via Google Imagen 2 (Google AI Studio API). No visible logo."
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help='Image generation prompt. E.g. "NYC skyline editorial photo"',
    )
    parser.add_argument(
        "--ratio",
        default="16:9",
        choices=VALID_RATIOS,
        help="Aspect ratio (default: 16:9)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
        help="Number of images to generate (default: 1, max: 4)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Imagen model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON (for n8n or scripting use)",
    )
    args = parser.parse_args()

    paths = generate_images(
        prompt=args.prompt,
        count=args.count,
        aspect_ratio=args.ratio,
        model=args.model,
    )

    if args.json:
        result = {
            "status": "success",
            "prompt": args.prompt,
            "aspect_ratio": args.ratio,
            "images": [str(p.resolve()) for p in paths],
        }
        print(json.dumps(result, indent=2))
    else:
        print()
        print(f"Done. {len(paths)} image(s) saved to data/output/images/")
        for p in paths:
            print(f"  file://{p.resolve()}")


if __name__ == "__main__":
    main()
