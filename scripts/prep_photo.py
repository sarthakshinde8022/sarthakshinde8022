#!/usr/bin/env python3
"""
Prep a source photo for ASCII conversion. Run once per photo (not part
of the daily automation):

    python scripts/prep_photo.py source-photo.jpg

A flatly-lit face converts to a dark, unreadable blob, so this does
three things first:
  1. Remove the background (rembg / u2net) so only the subject remains.
  2. Boost local contrast with CLAHE so a flat face gets real
     highlights and shadows.
  3. Composite onto pure white so the background maps to the blank end
     of the ASCII ramp (white -> spaces).

Output: source-prepped.png (grayscale), next to this script's parent dir.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

OUTPUT_NAME = "source-prepped.png"


def remove_background(input_path: Path) -> Image.Image:
    from rembg import remove  # imported lazily: heavy dep, only needed here

    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    from io import BytesIO

    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def boost_contrast_clahe(rgba: Image.Image) -> Image.Image:
    """Apply CLAHE (contrast-limited adaptive histogram equalization) to
    the luminance channel so flat lighting gets real local contrast."""
    rgb = np.array(rgba.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_boosted = clahe.apply(l_channel)

    lab_boosted = cv2.merge((l_boosted, a_channel, b_channel))
    rgb_boosted = cv2.cvtColor(lab_boosted, cv2.COLOR_LAB2RGB)

    out = Image.fromarray(rgb_boosted).convert("RGBA")
    out.putalpha(rgba.getchannel("A"))  # keep the original alpha (background cutout)
    return out


def composite_on_white(rgba: Image.Image) -> Image.Image:
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba)
    return composited.convert("L")  # grayscale


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <source-photo.jpg>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(__file__).parent.parent / OUTPUT_NAME

    print("Removing background...")
    cutout = remove_background(input_path)

    print("Boosting local contrast (CLAHE)...")
    boosted = boost_contrast_clahe(cutout)

    print("Compositing onto white + converting to grayscale...")
    final = composite_on_white(boosted)

    final.save(output_path)
    print(f"Wrote {output_path} ({final.size[0]}x{final.size[1]})")


if __name__ == "__main__":
    main()
