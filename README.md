# MisTools

Personal Windows toolbox — a local web app that runs PowerShell utilities through a clean browser UI. Built by Pato, powered by Claude.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey) ![Windows](https://img.shields.io/badge/Windows-10%2F11-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## Otras herramientas incluidas

Este repo también incluye una colección de scripts y utilidades independientes en [`otras-herramientas/`](./otras-herramientas): scraper de Mercado Libre con dashboard, procesamiento batch de imágenes, conversión de assets tarot, y descarga de historial de YouTube.

---

## What it does

MisTools is a lightweight local web dashboard for Windows maintenance tasks. It streams real-time output from PowerShell scripts directly into a terminal panel in your browser.

**Current tools:**

| Tool | Description |
|---|---|
| ClaudeCleaner | Temp files, browser caches, prefetch, recycle bin — with per-category checkboxes |
| Claude Antimalware | Windows Defender scans (Quick / Full / Custom path) |
| Disk Analyzer | Visual breakdown of folder sizes per drive |
| Startup Manager | Everything that launches at Windows startup |
| System Info | CPU, RAM, GPU, disks, network, top processes |

---

## Requirements

- Windows 10 or 11
- Python 3.8+ ([python.org](https://python.org) — enable "Add to PATH" during install)
- PowerShell 5.1+ (included in Windows)

---

## Quick start

```
1. Download or clone this repo
2. Double-click iniciar.bat
3. Browser opens at http://localhost:7777
```

`iniciar.bat` installs Flask automatically on first run.

Manual start:

```bash
pip install -r requirements.txt
python app.py
```

---

## Project structure

```
MisTools/
├── app.py              # Flask server — endpoints and script execution
├── index.html          # Single-page frontend (HTML/CSS/JS)
├── iniciar.bat         # Windows launcher — installs deps and starts server
├── requirements.txt    # Python dependencies
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md # System design and data flow
│   ├── TOOLS.md        # Each tool documented in detail
│   └── ROADMAP.md      # Planned features
└── ../Scripts/         # PowerShell scripts (live in %USERPROFILE%\Scripts)
    ├── ClaudeCleaner.ps1
    ├── ClaudeCleanerWeb.ps1
    ├── AntimalwareWeb.ps1
    ├── DiskAnalyzerWeb.ps1
    ├── StartupWeb.ps1
    └── SysInfoWeb.ps1
```

---

## How it works

1. **Frontend** sends a request to `/run/<tool_id>?param=value`
2. **Flask** spawns a PowerShell subprocess with the right script and parameters
3. **PowerShell** outputs structured lines (`TYPE|data|data|...`) to stdout
4. **Flask** streams those lines as Server-Sent Events (SSE)
5. **Frontend** parses each event type and renders it in the terminal panel

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full details.

---

## Adding a new tool

1. Create `%USERPROFILE%\Scripts\YourToolWeb.ps1` — output `TYPE|data` lines
2. Add an entry to `TOOLS` list in `app.py`
3. Add detail rows to `DETAILS` object in `index.html`
4. Add an options modal if the tool has configurable parameters
5. Reload the server

---

## License

MIT — do whatever you want with it.
