# ============================================================
#  ClaudeCleaner v2 - Limpieza automatica con detalle
#  Creado por Claude Code
# ============================================================

$Host.UI.RawUI.WindowTitle = "ClaudeCleaner - Limpieza en progreso..."
$logPath = "$env:USERPROFILE\Scripts\cleaner_log.txt"
$fecha   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$totalMB = 0
$totalArchivos = 0
$resumen = @()

# ── Helpers de color ────────────────────────────────────────
function Titulo($txt) {
    Write-Host ""
    Write-Host "  $txt" -ForegroundColor Cyan
    Write-Host "  $("─" * ($txt.Length))" -ForegroundColor DarkCyan
}

function Info($txt)    { Write-Host "    $txt" -ForegroundColor Gray }
function OK($txt)      { Write-Host "    $txt" -ForegroundColor Green }
function Dim($txt)     { Write-Host "    $txt" -ForegroundColor DarkGray }

function FormatSize($bytes) {
    if ($bytes -ge 1GB) { return "{0:N2} GB" -f ($bytes / 1GB) }
    if ($bytes -ge 1MB) { return "{0:N2} MB" -f ($bytes / 1MB) }
    if ($bytes -ge 1KB) { return "{0:N2} KB" -f ($bytes / 1KB) }
    return "$bytes B"
}

# ── Animacion "Working" ──────────────────────────────────────
function Spinner($mensaje, $bloque) {
    $frames  = @("⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏")
    $i       = 0
    $job     = Start-Job -ScriptBlock $bloque
    while ($job.State -eq "Running") {
        $frame = $frames[$i % $frames.Count]
        Write-Host "`r    $frame  $mensaje..." -NoNewline -ForegroundColor Yellow
        Start-Sleep -Milliseconds 80
        $i++
    }
    Write-Host "`r    ✓  $mensaje    " -ForegroundColor Green
    return Receive-Job $job
}

# ── Funcion principal de limpieza ───────────────────────────
function LimpiarCarpeta($nombre, $ruta, $paso, $total) {
    if (-not (Test-Path $ruta)) {
        Dim "$nombre → carpeta no encontrada, skip"
        return @{ MB = 0; Archivos = 0; Detalle = @() }
    }

    Write-Progress -Activity "ClaudeCleaner" `
        -Status "Limpiando: $nombre" `
        -PercentComplete (($paso / $total) * 100)

    # Listar archivos antes de borrar
    $archivos = Get-ChildItem $ruta -Recurse -Force -ErrorAction SilentlyContinue |
                Where-Object { -not $_.PSIsContainer }

    $cantidad = $archivos.Count
    $bytesTotal = ($archivos | Measure-Object -Property Length -Sum).Sum

    if ($cantidad -eq 0) {
        Dim "$nombre → ya estaba limpia"
        return @{ MB = 0; Archivos = 0; Detalle = @() }
    }

    Info "$nombre → encontrados $cantidad archivos ($(FormatSize $bytesTotal))"

    # Mostrar los 5 mas pesados
    $top5 = $archivos | Sort-Object Length -Descending | Select-Object -First 5
    foreach ($f in $top5) {
        $tam = FormatSize $f.Length
        Dim "      $(($f.Name).PadRight(45)) $tam"
    }
    if ($cantidad -gt 5) { Dim "      ... y $($cantidad - 5) archivos mas" }

    # Borrar
    Get-ChildItem $ruta -Recurse -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    $mbLiberados = [math]::Round($bytesTotal / 1MB, 2)
    OK "    Liberados: $(FormatSize $bytesTotal)  ($cantidad archivos)"

    return @{
        MB       = $mbLiberados
        Archivos = $cantidad
        Detalle  = @("${nombre}: $cantidad archivos, $(FormatSize $bytesTotal)")
    }
}

# ═══════════════════════════════════════════════════════════
#  INICIO
# ═══════════════════════════════════════════════════════════

Clear-Host
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║       ClaudeCleaner  v2.0                ║" -ForegroundColor Cyan
Write-Host "  ║       $fecha          ║" -ForegroundColor DarkCyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$zonas = @(
    @{ Nombre = "Temp usuario";          Ruta = $env:TEMP },
    @{ Nombre = "Temp sistema";          Ruta = "C:\Windows\Temp" },
    @{ Nombre = "Prefetch";              Ruta = "C:\Windows\Prefetch" },
    @{ Nombre = "Windows Update cache";  Ruta = "C:\Windows\SoftwareDistribution\Download" },
    @{ Nombre = "Minidumps";             Ruta = "C:\Windows\Minidump" },
    @{ Nombre = "Chrome cache";          Ruta = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache" },
    @{ Nombre = "Edge cache";            Ruta = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache" },
    @{ Nombre = "Thumbnails cache";      Ruta = "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" }
)

# Agregar perfiles Firefox si existen
$ffBase = "$env:APPDATA\Mozilla\Firefox\Profiles"
if (Test-Path $ffBase) {
    Get-ChildItem $ffBase -Directory | ForEach-Object {
        $zonas += @{ Nombre = "Firefox cache ($($_.Name.Substring(0,8))...)"; Ruta = "$($_.FullName)\cache2" }
    }
}

$paso = 0
foreach ($zona in $zonas) {
    $paso++
    Titulo $zona.Nombre
    $r = LimpiarCarpeta $zona.Nombre $zona.Ruta $paso $zonas.Count
    $totalMB       += $r.MB
    $totalArchivos += $r.Archivos
    $resumen       += $r.Detalle
}

# ── Papelera ────────────────────────────────────────────────
Titulo "Papelera de reciclaje"
Write-Progress -Activity "ClaudeCleaner" -Status "Vaciando papelera..." -PercentComplete 95
try {
    Clear-RecycleBin -Force -ErrorAction Stop
    OK "    Papelera vaciada correctamente"
    $resumen += "Papelera: vaciada"
} catch {
    Dim "    Papelera ya estaba vacia o sin permisos"
}

Write-Progress -Activity "ClaudeCleaner" -Completed

# ═══════════════════════════════════════════════════════════
#  RESUMEN FINAL
# ═══════════════════════════════════════════════════════════
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║            LIMPIEZA COMPLETADA           ║" -ForegroundColor Green
Write-Host ("  ║  Archivos borrados : {0,-21}║" -f $totalArchivos) -ForegroundColor Green
Write-Host ("  ║  Espacio liberado  : {0,-21}║" -f "$(FormatSize ($totalMB * 1MB))") -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Presiona cualquier tecla para cerrar..." -ForegroundColor DarkGray

# ── Guardar log ─────────────────────────────────────────────
$lineas  = @("", "========== $fecha ==========")
$lineas += $resumen
$lineas += "TOTAL: $totalArchivos archivos, $(FormatSize ($totalMB * 1MB))"
$lineas += "────────────────────────────────────"
Add-Content $logPath $lineas

$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
