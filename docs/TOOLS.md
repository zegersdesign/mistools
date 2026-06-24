# Tools Reference

## ClaudeCleaner

**Script:** `ClaudeCleanerWeb.ps1`  
**Parameter:** `-Zones` (comma-separated, default: all)

Cleans temporary and cache files that accumulate over time. Safe to run daily — everything it deletes regenerates automatically.

### Zones

| Zone ID | Path | What it is |
|---------|------|-----------|
| `temp_user` | `%TEMP%` | User session temp files |
| `temp_sys` | `C:\Windows\Temp` | System temp files |
| `prefetch` | `C:\Windows\Prefetch` | App preload data (regenerates) |
| `winupdate` | `C:\Windows\SoftwareDistribution\Download` | Downloaded update installers |
| `minidumps` | `C:\Windows\Minidump` | Crash dump files |
| `chrome` | `%LOCALAPPDATA%\Google\Chrome\...\Cache` | Chrome cached web data |
| `edge` | `%LOCALAPPDATA%\Microsoft\Edge\...\Cache` | Edge cached web data |
| `firefox` | `%APPDATA%\Mozilla\Firefox\Profiles\*\cache2` | Firefox cached web data |
| `thumbs` | `%LOCALAPPDATA%\Microsoft\Windows\Explorer` | File thumbnail cache |
| `recycle` | Recycle Bin | Deleted files |

### Scheduled task
ClaudeCleaner runs automatically daily at 10:00 AM via Windows Task Scheduler (requires one-time admin setup — see README).

---

## Claude Antimalware

**Script:** `AntimalwareWeb.ps1`  
**Parameters:** `-ScanType`, `-CustomPath`

Runs Windows Defender from the command line. No third-party software required.

### Scan types

| Type | Time | What it scans |
|------|------|--------------|
| `QuickScan` | 2–5 min | RAM, running processes, common threat locations |
| `FullScan` | 1–4 hours | Every file on the system drive |
| `CustomScan` | Varies | A specific folder you choose |

### Notes
- Threats found are **automatically quarantined by Defender** before the report appears
- Requires Windows Defender to be enabled
- Signature date shown — update if more than a few days old

---

## Disk Analyzer

**Script:** `DiskAnalyzerWeb.ps1`  
**Parameter:** `-Drive` (single letter, default: C)

Recursively measures folder sizes at the root of a drive and ranks the top 15.

### Output
- Drive summary (total / used / free per drive)
- Progress bar per folder while scanning
- Visual bar chart of top folders by size

### Notes
- Scan time: 1–3 min for C:\ depending on drive speed and size
- Does not delete anything — analysis only

---

## Startup Manager

**Script:** `StartupWeb.ps1`  
**Parameter:** `-Filter` (all / user / system)

Lists everything configured to run at Windows startup. Read-only.

### Sources checked

| Source | Filter |
|--------|--------|
| `HKCU\...\Run` | user |
| `HKCU\...\RunOnce` | user |
| `%APPDATA%\...\Startup` folder | user |
| `HKLM\...\Run` | system |
| `HKLM\...\RunOnce` | system |
| `HKLM\...\Run (WOW6432Node)` | system |
| `C:\ProgramData\...\Startup` folder | system |
| WMI `Win32_StartupCommand` | system |

### To disable an entry
Task Manager → Startup apps tab → right-click → Disable. MisTools does not modify startup entries.

---

## System Info

**Script:** `SysInfoWeb.ps1`  
**Parameter:** `-Sections` (comma-separated, default: all)

### Sections

| Section ID | Data shown |
|-----------|-----------|
| `os` | OS name, build number, architecture, uptime |
| `cpu` | Model, cores, threads, max frequency, current load % |
| `ram` | Total, used, free, usage percentage |
| `gpu` | Model, VRAM, driver version |
| `disk` | All drives: total, used, free, percentage |
| `net` | Active adapters: name, description, link speed, public IP |
| `procs` | Top 5 processes by CPU time and RAM usage |
