# Architecture

## Overview

MisTools is a 3-layer local application:

```
Browser (index.html)
      ↕  HTTP + Server-Sent Events
Flask server (app.py)
      ↕  subprocess stdin/stdout
PowerShell scripts (*.ps1)
      ↕  Windows APIs
OS (WMI, Registry, Defender, FileSystem)
```

No database. No cloud. Everything runs locally on port 7777.

---

## Data flow

### Startup
```
iniciar.bat
  → checks Python in PATH
  → pip install flask if missing
  → python app.py
      → threading.Timer(1.2s) → webbrowser.open(localhost:7777)
      → Flask listens on :7777
```

### Tool execution
```
User clicks "Opciones" → modal opens
User configures options → clicks "Ejecutar"
  → JS: new EventSource('/run/<id>?param=value')
  → Flask: /run/<id> route
      → builds ps_args from query params
      → subprocess.Popen(['powershell', '-File', script, ...args])
      → for each stdout line:
          → strip ANSI codes
          → split on '|' → { type, parts }
          → yield SSE: "data: {json}\n\n"
  → JS: onmessage handler
      → addLine(msg) → renders formatted div in terminal
      → on '__DONE__': resets button state
```

---

## PowerShell script protocol

Scripts communicate with the server via stdout using a pipe-delimited format:

```
TYPE|field1|field2|...
```

### Standard types (all scripts)
| Type | Fields | Meaning |
|------|--------|---------|
| `START` | timestamp | Script started |
| `INFO` | message | Informational message |
| `PROGRESS` | message | Long-running operation update |
| `END` | OK or FAIL | Script completed |
| `ERROR` | message | Fatal error |

### ClaudeCleaner types
| Type | Fields |
|------|--------|
| `FOUND` | name, count, size | Folder has files to clean |
| `FILE` | filename, size | Individual file (top 5) |
| `MORE` | "N archivos mas" | Remaining files not listed |
| `DONE` | name, size, count | Folder cleaned |
| `CLEAN` | name, reason | Folder was already clean |
| `SKIP` | name, reason | Folder not found |
| `TOTAL` | filecount, mb | Final summary |

### Claude Antimalware types
| Type | Fields |
|------|--------|
| `DEFENDER` | status fields | Defender health |
| `DEFS` | date, version | Signature info |
| `SAFE` | message | No threats found |
| `THREAT` | name, path | Threat detected |
| `TOTAL_THREATS` | count | Scan summary |

### Disk Analyzer types
| Type | Fields |
|------|--------|
| `DISK` | letter, total, used, free, pct | Drive summary |
| `SCANNING` | name, current, total | Progress update |
| `FOLDER` | name, bytes, formatted | Folder size result |

### Startup Manager types
| Type | Fields |
|------|--------|
| `ITEM` | name, command, source | Startup entry |
| `TOTAL_ITEMS` | count | Total found |

### System Info types
| Type | Fields |
|------|--------|
| `OS` | name, build, arch | OS info |
| `UPTIME` | duration, last boot | Uptime |
| `CPU` | name, cores, freq | CPU info |
| `CPU_LOAD` | percent | Current load |
| `RAM` | total, used, free, pct | Memory |
| `GPU` | name, vram, driver | Graphics |
| `DISK` | letter, total, used, free, pct | Drive |
| `NET` | name, desc, speed | Network adapter |
| `IP_PUBLIC` | ip | Public IP |
| `PROC` | name, cpu, ram | Top process |

---

## Frontend architecture

Single HTML file — no framework, no build step.

Key JS structures:
- `tools[]` — loaded from `/tools` on init
- `DETAILS{}` — static detail text per tool id
- `src` — the active EventSource instance (only one at a time)
- `checked` (Set) — selected ClaudeCleaner zones
- `scanType` — selected antimalware scan mode
- `selectedDrive` — selected disk for analyzer
- `startupFilter` — startup manager filter
- `siChecked` (Set) — selected SysInfo sections

Key functions:
- `render(list)` — builds tool cards from tools array
- `openOpts(id)` — routes to the right modal opener
- `runWithUrl(id, name, url)` — starts SSE stream
- `addLine(msg, toolId)` — renders one terminal line
- `toggleDetail(id)` — show/hide card detail section

---

## Flask routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Serves index.html |
| `/tools` | GET | Returns TOOLS list as JSON |
| `/drives` | GET | Returns available drives with usage stats |
| `/run/<tool_id>` | GET | Starts SSE stream for a tool |

### /run query parameters
| Tool | Params |
|------|--------|
| `cleaner` | `zones` (comma-separated zone ids) |
| `antimalware` | `scantype` (QuickScan/FullScan/CustomScan), `custompath` |
| `diskanalyzer` | `drive` (single letter) |
| `startup` | `filter` (all/user/system) |
| `sysinfo` | `sections` (comma-separated section ids) |

---

## Security considerations

- Runs on localhost only — not exposed to network
- No authentication (single-user local app by design)
- PowerShell scripts run with current user privileges — admin required for system-level operations
- Input parameters are passed directly to PS scripts — safe for local use, would need sanitization for multi-user deployment
