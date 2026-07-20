"""
convert_to_coloring.py
Converts a colored tarot card into a clean B&W coloring book version.

Mode A (threshold): simple grayscale threshold
Mode B (edges):     detects color boundaries — best for flat-color illustrations
"""

from PIL import Image, ImageFilter, ImageOps, ImageChops
import sys
import os


def convert_threshold(input_path, output_path, threshold=180):
    """Mode A: grayscale + threshold."""
    img = Image.open(input_path).convert("RGB")
    gray = img.convert("L")
    gray = gray.filter(ImageFilter.GaussianBlur(radius=0.5))
    bw = gray.point(lambda p: 0 if p < threshold else 255, "L")
    bw.convert("RGB").save(output_path, "PNG")
    print("Saved (mode A):", output_path)


def convert_edges(input_path, output_path, sensitivity=25, line_thickness=2):
    """
    Mode B: color edge detection.
    Detects boundaries between different colors — works great for
    flat-color illustrations like Marseille tarot.

    sensitivity:      lower = only strong edges (cleaner but may miss fine lines)
                      higher = more edges detected (more detail, more noise)
                      recommended: 20-35
    line_thickness:   1 = very thin lines, 2-3 = good for coloring apps
    """
    img = Image.open(input_path).convert("RGB")

    # Detect edges in each color channel separately
    r, g, b = img.split()

    edges_r = r.filter(ImageFilter.FIND_EDGES)
    edges_g = g.filter(ImageFilter.FIND_EDGES)
    edges_b = b.filter(ImageFilter.FIND_EDGES)

    # Combine: a pixel is an edge if ANY channel shows an edge
    combined = ImageChops.lighter(
        ImageChops.lighter(edges_r, edges_g),
        edges_b
    )

    # Threshold to make edges crisp (remove faint noise)
    edge_mask = combined.point(lambda p: 255 if p > sensitivity else 0, "L")

    # Thicken lines so flood fill doesn't leak between thin gaps
    for _ in range(line_thickness - 1):
        edge_mask = edge_mask.filter(ImageFilter.MaxFilter(3))

    # Invert: edges become black, background becomes white
    result = ImageOps.invert(edge_mask).convert("RGB")
    result.save(output_path, "PNG")
    print("Saved (mode B):", output_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_to_coloring.py <input> <output> [mode] [value]")
        print("  mode A (threshold): python convert_to_coloring.py card.png out.png A 180")
        print("  mode B (edges):     python convert_to_coloring.py card.png out.png B 25")
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2]
    mode        = sys.argv[3].upper() if len(sys.argv) > 3 else "B"
    value       = int(sys.argv[4]) if len(sys.argv) > 4 else (180 if mode == "A" else 25)

    if not os.path.exists(input_file):
        print("File not found:", input_file)
        sys.exit(1)

    if mode == "A":
        convert_threshold(input_file, output_file, threshold=value)
    else:
        convert_edges(input_file, output_file, sensitivity=value)
