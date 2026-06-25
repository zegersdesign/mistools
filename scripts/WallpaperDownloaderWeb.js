#!/usr/bin/env node
// MisTools — Wallpaper Downloader
// Salida: TYPE|parte1|parte2|... (SSE para app.py)
// Uso: node WallpaperDownloaderWeb.js <URL> [carpeta]

const https = require("https");
const http  = require("http");
const fs    = require("fs");
const path  = require("path");

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
  "Accept-Language": "en-US,en;q=0.9",
  Accept: "text/html,application/xhtml+xml,*/*;q=0.8",
  Referer: "https://www.google.com/",
};

const IMAGE_EXTS = new Set([".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif"]);
const MIN_KB = 50;

function out(type, ...parts) {
  // Sanitizar pipes en partes para no romper el protocolo
  const safe = parts.map(p => String(p).replace(/\|/g, " "));
  process.stdout.write([type, ...safe].join("|") + "\n");
}

function isImageUrl(rawUrl) {
  try {
    const ext = path.extname(new URL(rawUrl).pathname).toLowerCase();
    return IMAGE_EXTS.has(ext);
  } catch { return false; }
}

function resolveUrl(base, rel) {
  try { return new URL(rel, base).href; } catch { return null; }
}

function slugify(rawUrl) {
  try {
    const p = new URL(rawUrl);
    return (p.hostname + p.pathname).replace(/[^\w-]/g, "_").replace(/_+/g, "_").slice(0, 60);
  } catch { return "wallpapers"; }
}

function uniquePath(dir, imgUrl) {
  let name = path.basename(new URL(imgUrl).pathname) || "wallpaper.jpg";
  if (name.length < 4) name = Date.now() + (path.extname(imgUrl) || ".jpg");
  let dest = path.join(dir, name);
  let i = 1;
  while (fs.existsSync(dest)) {
    const { name: stem, ext } = path.parse(name);
    dest = path.join(dir, `${stem}_${i++}${ext}`);
  }
  return dest;
}

function fetchUrl(rawUrl, binary = false, maxRedirects = 10) {
  return new Promise((resolve, reject) => {
    let parsed;
    try { parsed = new URL(rawUrl); } catch (e) { return reject(new Error(`URL inválida: ${rawUrl}`)); }
    const lib = parsed.protocol === "https:" ? https : http;
    const req = lib.get(rawUrl, { headers: HEADERS, timeout: 20000 }, (res) => {
      if ([301, 302, 303, 307, 308].includes(res.statusCode)) {
        if (maxRedirects <= 0) return reject(new Error("Demasiadas redirecciones"));
        const loc = res.headers.location;
        res.resume();
        return fetchUrl(resolveUrl(rawUrl, loc) || loc, binary, maxRedirects - 1)
          .then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => {
        const buf = Buffer.concat(chunks);
        resolve({
          data: binary ? buf : buf.toString("utf8"),
          contentType: res.headers["content-type"] || "",
          contentLength: parseInt(res.headers["content-length"] || "0", 10),
        });
      });
      res.on("error", reject);
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(); reject(new Error("Timeout")); });
  });
}

function extractImageUrls(html, baseUrl) {
  const found = new Set();
  const add = (raw) => {
    if (!raw || raw.startsWith("data:")) return;
    const abs = resolveUrl(baseUrl, raw.trim());
    if (abs && isImageUrl(abs)) found.add(abs);
  };
  // <img> con varios atributos lazy-load
  for (const m of html.matchAll(/<img[^>]+>/gi)) {
    for (const attr of ["src", "data-src", "data-lazy-src", "data-original", "data-url", "data-full"]) {
      const v = m[0].match(new RegExp(`${attr}=["']([^"']+)["']`, "i"));
      if (v) add(v[1]);
    }
  }
  // <a href> apuntando a imágenes
  for (const m of html.matchAll(/href=["']([^"']+)["']/gi)) add(m[1]);
  // og:image / twitter:image
  for (const m of html.matchAll(/<meta[^>]+>/gi)) {
    if (/og:image|twitter:image/.test(m[0])) {
      const c = m[0].match(/content=["']([^"']+)["']/i);
      if (c) add(c[1]);
    }
  }
  // background-image: url(...)
  for (const m of html.matchAll(/url\(["']?(https?:\/\/[^"')]+)["']?\)/gi)) add(m[1]);
  // URLs desnudas en scripts/JSON
  for (const m of html.matchAll(/https?:\/\/[^\s"'<>,\)]+\.(?:jpg|jpeg|png|webp|gif|bmp|avif)/gi)) add(m[0]);
  return [...found];
}

function extractNextPages(html, baseUrl) {
  const pages = new Set();
  let origin;
  try { origin = new URL(baseUrl).hostname; } catch { return []; }
  for (const m of html.matchAll(/href=["']([^"']+)["']/gi)) {
    const abs = resolveUrl(baseUrl, m[1]);
    if (!abs) continue;
    try {
      const u = new URL(abs);
      if (u.hostname === origin && abs !== baseUrl && /\/p\/\d+|[?&]page=\d+|[?&]p=\d+/.test(abs))
        pages.add(abs);
    } catch {}
  }
  return [...pages];
}

async function downloadImage(imgUrl, destFile) {
  const res = await fetchUrl(imgUrl, true);
  if (!res.contentType.includes("image") && !isImageUrl(imgUrl)) return false;
  if (res.contentLength > 0 && res.contentLength < MIN_KB * 1024) return false;
  if (res.data.length < MIN_KB * 1024) return false;
  fs.writeFileSync(destFile, res.data);
  return true;
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function main() {
  const args = process.argv.slice(2);
  if (!args[0]) { out("ERROR", "No se proporcionó URL"); process.exit(1); }

  let targetUrl = args[0];
  if (!targetUrl.startsWith("http")) targetUrl = "https://" + targetUrl;

  const folderArg  = args[1] || slugify(targetUrl);
  const destDir    = path.resolve(folderArg);
  fs.mkdirSync(destDir, { recursive: true });

  out("START", "Wallpaper Downloader");
  out("WP_DEST", destDir);
  out("INFO", `Escaneando ${targetUrl}`);

  let html;
  try {
    const res = await fetchUrl(targetUrl);
    html = res.data;
  } catch (e) {
    out("ERROR", `No se pudo cargar la página: ${e.message}`);
    out("END");
    return;
  }

  let allImages = extractImageUrls(html, targetUrl);

  const extraPages = extractNextPages(html, targetUrl);
  if (extraPages.length) {
    out("PROGRESS", `Encontradas ${extraPages.length} páginas adicionales`);
    for (const pg of extraPages) {
      out("PROGRESS", `Explorando página extra...`);
      try {
        const { data: pgHtml } = await fetchUrl(pg);
        allImages.push(...extractImageUrls(pgHtml, pg));
        await sleep(400);
      } catch {}
    }
  }

  allImages = [...new Set(allImages)];
  out("WP_FOUND", allImages.length);

  if (allImages.length === 0) {
    out("INFO", "No se encontraron imágenes descargables en esta URL.");
    out("END");
    return;
  }

  let ok = 0, skip = 0;
  for (let i = 0; i < allImages.length; i++) {
    const imgUrl = allImages[i];
    let label;
    try { label = path.basename(new URL(imgUrl).pathname).slice(0, 50) || "imagen"; }
    catch { label = "imagen"; }

    out("WP_DL", i + 1, allImages.length, label);
    try {
      const dest = uniquePath(destDir, imgUrl);
      const downloaded = await downloadImage(imgUrl, dest);
      if (downloaded) {
        out("WP_OK", label);
        ok++;
      } else {
        out("WP_SKIP", label);
        skip++;
      }
    } catch (e) {
      out("WP_ERR", label, e.message.slice(0, 60));
      skip++;
    }
    await sleep(300);
  }

  out("WP_TOTAL", ok, skip, destDir);
  out("END");
}

main().catch((e) => { out("ERROR", e.message); process.exit(1); });
