# image-blaster

Drop images in `input/`, run `node blast.js`, get all variants in `output/<variant>/`.

## Usage

```
node blast.js                  # all variants
node blast.js bw edges         # only these
node blast.js --clean          # wipe output/ first
```

## Variants

| Name    | What it does                              |
|---------|-------------------------------------------|
| `bw`    | Greyscale + threshold (coloring book)     |
| `edges` | Sobel edge detection (line art)           |
| `thumb` | Resize to 512px (fit inside)              |
| `webp`  | WebP @ quality 80                         |

Tune parameters in the `VARIANTS` object at the top of `blast.js`.
