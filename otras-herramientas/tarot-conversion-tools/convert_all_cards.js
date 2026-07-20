// convert_all_cards.js
// Converts a folder of colored tarot cards to B&W coloring book versions.
//
// Usage:
//   node convert_all_cards.js <input_folder> <output_folder>
//
// Example:
//   node convert_all_cards.js "cartas tarot jodo" "cartas tarot bw"

const sharp  = require('sharp');
const fs     = require('fs');
const path   = require('path');

const SUPPORTED = ['.png', '.jpg', '.jpeg', '.webp'];

async function convertCard(inputPath, outputPath) {
  await sharp(inputPath)
    .greyscale()          // convert to grayscale
    .threshold(50)        // pixels darker than 50 → black, rest → white
    .png()
    .toFile(outputPath);
}

async function convertFolder(inputFolder, outputFolder) {
  if (!fs.existsSync(inputFolder)) {
    console.error('Input folder not found:', inputFolder);
    process.exit(1);
  }

  fs.mkdirSync(outputFolder, { recursive: true });

  const files = fs.readdirSync(inputFolder).filter(f =>
    SUPPORTED.includes(path.extname(f).toLowerCase())
  );

  if (files.length === 0) {
    console.error('No images found in:', inputFolder);
    process.exit(1);
  }

  console.log(`Found ${files.length} cards. Converting...`);
  console.log('-'.repeat(40));

  let ok = 0, errors = 0;
  for (const filename of files.sort()) {
    const inputPath  = path.join(inputFolder, filename);
    const outputName = path.parse(filename).name + '_bw.png';
    const outputPath = path.join(outputFolder, outputName);
    try {
      await convertCard(inputPath, outputPath);
      console.log('  OK ', filename, '->', outputName);
      ok++;
    } catch (e) {
      console.log('  ERR', filename, ':', e.message);
      errors++;
    }
  }

  console.log('-'.repeat(40));
  console.log(`Done! ${ok} converted, ${errors} errors.`);
  console.log('Output folder:', path.resolve(outputFolder));
}

const [,, inputFolder, outputFolder] = process.argv;
if (!inputFolder || !outputFolder) {
  console.log('Usage: node convert_all_cards.js <input_folder> <output_folder>');
  process.exit(1);
}

convertFolder(inputFolder, outputFolder);
