// image-blaster / blast.js
// Drop images in image-blaster/input/, run this, get processed variants in output/.
//
// Usage:
//   node blast.js                  -> run ALL variants
//   node blast.js bw edges         -> run only those variants
//   node blast.js --clean          -> wipe output/ before processing
//   node blast.js --clean bw       -> wipe output/, then run bw
//
// Variants:
//   bw     - greyscale + threshold (coloring book style)
//   edges  - Sobel edge detection (line art)
//   thumb  - 512px thumbnail
//   webp   - WebP @ quality 80

const sharp = require('sharp');
const fs    = require('fs');
const path  = require('path');

const SUPPORTED = ['.png', '.jpg', '.jpeg', '.webp'];
const ROOT      = __dirname;
const INPUT     = path.join(ROOT, 'input');
const OUTPUT    = path.join(ROOT, 'output');

const VARIANTS = {
  bw: {
    ext: '.png',
    apply: async (inputPath) =>
      sharp(inputPath).greyscale().threshold(180).png(),
  },
  edges: {
    // Sobel on raw greyscale pixels. sharp's convolve clamps signed results
    // to 0-255 which loses half the gradient information, so we do it by
    // hand: combine Sobel X and Y, threshold the magnitude, draw black edges
    // on white background.
    ext: '.png',
    apply: async (inputPath) => {
      const { data, info } = await sharp(inputPath)
        .greyscale()
        .blur(0.5)
        .raw()
        .toBuffer({ resolveWithObject: true });

      const { width, height } = info;
      const out = Buffer.alloc(width * height, 255); // start white

      for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
          const i = y * width + x;
          const tl = data[i - width - 1], tc = data[i - width], tr = data[i - width + 1];
          const ml = data[i - 1],          mr = data[i + 1];
          const bl = data[i + width - 1], bc = data[i + width], br = data[i + width + 1];
          const gx = -tl + tr - 2 * ml + 2 * mr - bl + br;
          const gy = -tl - 2 * tc - tr + bl + 2 * bc + br;
          const mag = Math.sqrt(gx * gx + gy * gy);
          if (mag > 30) out[i] = 0; // black edge
        }
      }

      return sharp(out, { raw: { width, height, channels: 1 } }).png();
    },
  },
  thumb: {
    ext: '.png',
    apply: async (inputPath) =>
      sharp(inputPath).resize(512, 512, { fit: 'inside' }).png(),
  },
  webp: {
    ext: '.webp',
    apply: async (inputPath) =>
      sharp(inputPath).webp({ quality: 80 }),
  },
};

function parseArgs(argv) {
  const args  = argv.slice(2);
  const clean = args.includes('--clean');
  const names = args.filter(a => !a.startsWith('--'));
  const variants = names.length ? names : Object.keys(VARIANTS);

  for (const v of variants) {
    if (!VARIANTS[v]) {
      console.error(`Unknown variant: ${v}`);
      console.error(`Available: ${Object.keys(VARIANTS).join(', ')}`);
      process.exit(1);
    }
  }
  return { variants, clean };
}

async function blastOne(inputPath, baseName, variants) {
  const results = {};
  for (const v of variants) {
    const def    = VARIANTS[v];
    const outDir = path.join(OUTPUT, v);
    fs.mkdirSync(outDir, { recursive: true });
    const outPath = path.join(outDir, `${baseName}_${v}${def.ext}`);
    try {
      const pipeline = await def.apply(inputPath);
      await pipeline.toFile(outPath);
      results[v] = 'OK';
    } catch (e) {
      results[v] = `ERR ${e.message}`;
    }
  }
  return results;
}

async function main() {
  const { variants, clean } = parseArgs(process.argv);

  if (!fs.existsSync(INPUT)) {
    console.error('Input folder not found:', INPUT);
    process.exit(1);
  }

  if (clean && fs.existsSync(OUTPUT)) {
    fs.rmSync(OUTPUT, { recursive: true, force: true });
    console.log('Cleaned output/');
  }
  fs.mkdirSync(OUTPUT, { recursive: true });

  const files = fs.readdirSync(INPUT)
    .filter(f => SUPPORTED.includes(path.extname(f).toLowerCase()))
    .sort();

  if (files.length === 0) {
    console.error('No images in:', INPUT);
    process.exit(1);
  }

  console.log(`Blasting ${files.length} image(s) -> [${variants.join(', ')}]`);
  console.log('-'.repeat(60));

  let totalOk = 0, totalErr = 0;
  for (const filename of files) {
    const baseName  = path.parse(filename).name;
    const inputPath = path.join(INPUT, filename);
    const results   = await blastOne(inputPath, baseName, variants);

    const summary = variants
      .map(v => `${v}:${results[v].startsWith('OK') ? 'OK' : 'ERR'}`)
      .join(' ');
    console.log(`  ${filename}  ${summary}`);

    for (const v of variants) {
      if (results[v] === 'OK') totalOk++;
      else { totalErr++; console.log(`    ${v}: ${results[v]}`); }
    }
  }

  console.log('-'.repeat(60));
  console.log(`Done. ${totalOk} OK, ${totalErr} errors.`);
  console.log('Output:', OUTPUT);
}

main();
