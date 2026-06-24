param([string]$Zones = "all")

$selected = if ($Zones -eq "all") {
    @("temp_user","temp_sys","prefetch","winupdate","minidumps","chrome","edge","firefox","thumbs","recycle")
} else {
    $Zones -split ","
}

function Has($z) { return $selected -contains $z }

$totalMB    = 0
$totalFiles = 0

function FormatSize($bytes) {
    if ($bytes -ge 1GB) { return "{0:N1} GB" -f ($bytes/1GB) }
    if ($bytes -ge 1MB) { return "{0:N1} MB" -f ($bytes/1MB) }
    if ($bytes -ge 1KB) { return "{0:N1} KB" -f ($bytes/1KB) }
    return "$bytes B"
}

function Limpiar($id, $nombre, $ruta) {
    if (-not (Has $id)) { return }
    if (-not (Test-Path $ruta)) {
        Write-Output "SKIP|$nombre|no encontrada"
        return
    }
    $archivos = Get-ChildItem $ruta -Recurse -Force -ErrorAction SilentlyContinue |
                Where-Object { -not $_.PSIsContainer }
    $count = $archivos.Count
    $bytes = ($archivos | Measure-Object -Property Length -Sum).Sum
    if ($count -eq 0) {
        Write-Output "CLEAN|$nombre|ya estaba limpia"
        return
    }
    Write-Output "FOUND|$nombre|$count archivos|$(FormatSize $bytes)"
    $archivos | Sort-Object Length -Descending | Select-Object -First 5 | ForEach-Object {
        Write-Output "FILE|$($_.Name)|$(FormatSize $_.Length)"
    }
    if ($count -gt 5) { Write-Output "MORE|$($count - 5) archivos mas" }
    Get-ChildItem $ruta -Recurse -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    $mb = [math]::Round($bytes/1MB, 2)
    $script:totalMB    += $mb
    $script:totalFiles += $count
    Write-Output "DONE|$nombre|$(FormatSize $bytes)|$count archivos"
}

Write-Output "START|$(Get-Date -Format 'HH:mm:ss')"

Limpiar "temp_user"   "Temp usuario"         $env:TEMP
Limpiar "temp_sys"    "Temp sistema"         "C:\Windows\Temp"
Limpiar "prefetch"    "Prefetch"             "C:\Windows\Prefetch"
Limpiar "winupdate"   "Windows Update cache" "C:\Windows\SoftwareDistribution\Download"
Limpiar "minidumps"   "Minidumps"            "C:\Windows\Minidump"
Limpiar "chrome"      "Chrome cache"         "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
Limpiar "edge"        "Edge cache"           "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
Limpiar "thumbs"      "Thumbnails"           "$env:LOCALAPPDATA\Microsoft\Windows\Explorer"

if (Has "firefox") {
    $ffBase = "$env:APPDATA\Mozilla\Firefox\Profiles"
    if (Test-Path $ffBase) {
        Get-ChildItem $ffBase -Directory | ForEach-Object {
            Limpiar "firefox" "Firefox cache" "$($_.FullName)\cache2"
        }
    } else {
        Write-Output "SKIP|Firefox cache|no instalado"
    }
}

if (Has "recycle") {
    try {
        Clear-RecycleBin -Force -ErrorAction Stop
        Write-Output "DONE|Papelera|vaciada|—"
    } catch {
        Write-Output "CLEAN|Papelera|ya estaba vacia"
    }
}

Write-Output "TOTAL|$totalFiles|$([math]::Round($totalMB,2))"
Write-Output "END|OK"
