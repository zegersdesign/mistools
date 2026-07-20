"""
convert_all_cards.py
Converts an entire folder of colored tarot cards to B&W coloring book versions.

Usage:
    python convert_all_cards.py <input_folder> <output_folder>

Example:
    python convert_all_cards.py "cartas tarot jodo" "cartas tarot bw"

- Processes all PNG and JPG files in the input folder
- Saves B&W versions to the output folder (creates it if needed)
- Uses threshold 50 (keeps only original black lines, removes all color)
"""

from PIL import Image, ImageFilter
import os
import sys

THRESHOLD = 50   # Only keeps pixels darker than this → pure black lines only
                 # Change to 40 if lines are too faint, 60 if too much black remains

SUPPORTED = ('.png', '.jpg', '.jpeg', '.webp')


def convert_card(input_path: str, output_path: str):
    img = Image.open(input_path).convert("RGB")
    gray = img.convert("L")
    gray = gray.filter(ImageFilter.GaussianBlur(radius=0.5))
    bw = gray.point(lambda p: 0 if p < THRESHOLD else 255, "L")
    bw.convert("RGB").save(output_path, "PNG")


def convert_folder(input_folder: str, output_folder: str):
    if not os.path.isdir(input_folder):
        print("Input folder not found:", input_folder)
        sys.exit(1)

    os.makedirs(output_folder, exist_ok=True)

    files = [f for f in os.listdir(input_folder)
             if os.path.splitext(f)[1].lower() in SUPPORTED]

    if not files:
        print("No images found in:", input_folder)
        sys.exit(1)

    print(f"Found {len(files)} cards. Converting...")
    print("-" * 40)

    ok = 0
    errors = 0
    for filename in sorted(files):
        input_path  = os.path.join(input_folder, filename)
        output_name = os.path.splitext(filename)[0] + "_bw.png"
        output_path = os.path.join(output_folder, output_name)
        try:
            convert_card(input_path, output_path)
            print(f"  OK  {filename} -> {output_name}")
            ok += 1
        except Exception as e:
            print(f"  ERR {filename}: {e}")
            errors += 1

    print("-" * 40)
    print(f"Done! {ok} converted, {errors} errors.")
    print(f"Output folder: {os.path.abspath(output_folder)}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    convert_folder(sys.argv[1], sys.argv[2])
