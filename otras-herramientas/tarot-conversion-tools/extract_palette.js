// extract_palette.js
// Scans all colored tarot cards and extracts the real color palette used.
// Skips near-black (outlines) and near-white (paper background).
// Groups similar colors together and ranks by how much they appear.
//
// Usage:
//   node extract_palette.js "cartas tarot jodo"

const sharp = require('sharp');
const fs    = require('fs');
const path  = require('path');

const SUPPORTED = ['.png', '.jpg', '.jpeg', '.webp'];

// ── Tuning ────────────────────────────────────────────────────
const SAMPLE_STEP   = 4;    // sample every Nth pixel (4 = fast, 1 = exact)
const MIN_LIGHTNESS = 20;   // skip near-black pixels (outlines)
const MAX_LIGHTNESS = 92;   // skip near-white pixels (paper background)
const MIN_SATURATION= 18;   // skip gray/neutral pixels
const BUCKET_SIZE   = 24;   // group colors within this RGB distance into one bucket
const TOP_COLORS    = 14;   // how many final colors to output
// ─────────────────────────────────────────────────────────────

function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return [h * 360, s * 100, l * 100];
}

function toHex(r, g, b) {
  return '#' + [r, g, b].map(v => Math.min(255, Math.max(0, v)).toString(16).padStart(2, '0')).join('').toUpperCase();
}

function colorDistance(r1, g1, b1, r2, g2, b2) {
  return Math.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2);
}

async function scanImage(imgPath, colorMap) {
  const { data, info } = await sharp(imgPath)
    .raw()
    .toBuffer({ resolveWithObject: true });

  const channels = info.channels; // 3 or 4

  for (let i = 0; i < data.length; i += channels * SAMPLE_STEP) {
    const r = data[i], g = data[i+1], b = data[i+2];
    const [, s, l] = rgbToHsl(r, g, b);

    // Skip outlines, background, and gray neutrals
    if (l < MIN_LIGHTNESS || l > MAX_LIGHTNESS) continue;
    if (s < MIN_SATURATION) continue;

    // Quantize to a bucket key (round to nearest BUCKET_SIZE, clamp to 255)
    const br = Math.min(255, Math.round(r / BUCKET_SIZE) * BUCKET_SIZE);
    const bg = Math.min(255, Math.round(g / BUCKET_SIZE) * BUCKET_SIZE);
    const bb = Math.min(255, Math.round(b / BUCKET_SIZE) * BUCKET_SIZE);
    const key = `${br},${bg},${bb}`;

    colorMap.set(key, (colorMap.get(key) || 0) + 1);
  }
}

function mergeBuckets(colorMap) {
  // Convert map to array of { r, g, b, count }
  const entries = [];
  for (const [key, count] of colorMap.entries()) {
    const [r, g, b] = key.split(',').map(Number);
    entries.push({ r, g, b, count });
  }
  entries.sort((a, b) => b.count - a.count);

  // Greedy merge: absorb nearby colors into the dominant one
  const merged = [];
  const used = new Set();

  for (let i = 0; i < entries.length; i++) {
    if (used.has(i)) continue;
    const base = { ...entries[i] };
    for (let j = i + 1; j < entries.length; j++) {
      if (used.has(j)) continue;
      const dist = colorDistance(base.r, base.g, base.b, entries[j].r, entries[j].g, entries[j].b);
      if (dist <= BUCKET_SIZE * 1.5) {
        base.count += entries[j].count;
        used.add(j);
      }
    }
    merged.push(base);
    used.add(i);
  }

  merged.sort((a, b) => b.count - a.count);
  return merged;
}

async function main() {
  const inputFolder = process.argv[2];
  if (!inputFolder) {
    console.log('Usage: node extract_palette.js <input_folder>');
    process.exit(1);
  }
  if (!fs.existsSync(inputFolder)) {
    console.error('Folder not found:', inputFolder);
    process.exit(1);
  }

  const files = fs.readdirSync(inputFolder)
    .filter(f => SUPPORTED.includes(path.extname(f).toLowerCase()));

  if (files.length === 0) {
    console.error('No images found in:', inputFolder);
    process.exit(1);
  }

  console.log(`Scanning ${files.length} cards for colors...`);
  console.log('(This may take a few seconds)\n');

  const colorMap = new Map();

  for (const filename of files) {
    const imgPath = path.join(inputFolder, filename);
    try {
      await scanImage(imgPath, colorMap);
      process.stdout.write('.');
    } catch (e) {
      process.stdout.write('x');
    }
  }

  console.log('\n');

  const merged = mergeBuckets(colorMap);
  const top = merged.slice(0, TOP_COLORS);
  const total = top.reduce((s, c) => s + c.count, 0);

  console.log(`TOP ${TOP_COLORS} COLORS FOUND IN THE DECK:`);
  console.log('='.repeat(50));

  const dartColors = [];
  for (const c of top) {
    const hex = toHex(c.r, c.g, c.b);
    const pct = ((c.count / total) * 100).toFixed(1);
    const [h, s, l] = rgbToHsl(c.r, c.g, c.b);
    const label = guessColorName(h, s, l);
    console.log(`  ${hex}  ${label.padEnd(20)} ${pct}%`);
    dartColors.push({ hex, label, r: c.r, g: c.g, b: c.b });
  }

  console.log('\n' + '='.repeat(50));
  console.log('\nDart color list (copy into colors_data.dart):\n');
  console.log('const List<Color> tarotPalette = [');
  for (const c of dartColors) {
    const hex6 = c.hex.replace('#', '');
    console.log(`  Color(0xFF${hex6}), // ${c.label}`);
  }
  console.log('];\n');

  // Also save to a JSON file for reference
  const outPath = path.join(inputFolder, '..', 'palette.json');
  fs.writeFileSync(outPath, JSON.stringify(dartColors, null, 2));
  console.log('Full palette saved to:', path.resolve(outPath));
}

function guessColorName(h, s, l) {
  if (s < 15) return l < 40 ? 'Dark Gray' : 'Light Gray';
  // Skin / flesh tones: orange hue + high lightness
  if (h >= 20 && h < 45 && l > 70) return 'Skin';
  if (h < 15  || h >= 345) return l < 45 ? 'Dark Red'    : 'Red';
  if (h < 20)               return l < 45 ? 'Brown'       : 'Skin';
  if (h < 45)               return l < 45 ? 'Brown'       : 'Orange';
  if (h < 65)               return l < 70 ? 'Gold/Olive'  : 'Yellow';
  if (h < 150)              return l < 45 ? 'Dark Green'  : 'Green';
  if (h < 195)              return l < 45 ? 'Dark Teal'   : 'Teal';
  if (h < 255)              return l < 50 ? 'Dark Blue'   : 'Light Blue';
  if (h < 285)              return l < 45 ? 'Dark Purple' : 'Purple';
  if (h < 330)              return l < 45 ? 'Dark Pink'   : 'Pink';
  return 'Rose';
}

main();
