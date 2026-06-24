param([string]$Drive = "C")

Write-Output "START|$(Get-Date -Format 'HH:mm:ss')"

$root = "${Drive}:\"
if (-not (Test-Path $root)) {
    Write-Output "ERROR|Disco $Drive no encontrado"
    Write-Output "END|FAIL"
    exit
}

Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Used -ne $null -and ($_.Used + $_.Free) -gt 0) {
        $totalGB = [math]::Round(($_.Used + $_.Free) / 1GB, 1)
        $usedGB  = [math]::Round($_.Used / 1GB, 1)
        $freeGB  = [math]::Round($_.Free / 1GB, 1)
        $pct     = [math]::Round(($_.Used / ($_.Used + $_.Free)) * 100)
        Write-Output "DISK|$($_.Name):|$totalGB GB total|$usedGB GB usado|$freeGB GB libre|$pct%"
    }
}

Write-Output "INFO|Analizando carpetas de ${Drive}:\..."

$carpetas = Get-ChildItem $root -Directory -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notin @('$Recycle.Bin','System Volume Information') }

$resultados = @()
$total = $carpetas.Count
$i = 0

foreach ($c in $carpetas) {
    $i++
    Write-Output "SCANNING|$($c.Name)|$i|$total"
    [Console]::Out.Flush()
    try {
        $bytes = (Get-ChildItem $c.FullName -Recurse -Force -ErrorAction SilentlyContinue |
                  Measure-Object -Property Length -Sum).Sum
        if (-not $bytes) { $bytes = 0 }
    } catch { $bytes = 0 }
    $resultados += [PSCustomObject]@{ Nombre = $c.Name; Bytes = $bytes }
}

Write-Output "INFO|Top carpetas por tamano en ${Drive}:\:"
$resultados | Sort-Object Bytes -Descending | Select-Object -First 15 | ForEach-Object {
    if ($_.Bytes -ge 1GB)     { $tam = "{0:N1} GB" -f ($_.Bytes/1GB) }
    elseif ($_.Bytes -ge 1MB) { $tam = "{0:N0} MB" -f ($_.Bytes/1MB) }
    elseif ($_.Bytes -ge 1KB) { $tam = "{0:N0} KB" -f ($_.Bytes/1KB) }
    else                      { $tam = "$($_.Bytes) B" }
    Write-Output "FOLDER|$($_.Nombre)|$($_.Bytes)|$tam"
}

Write-Output "END|OK"
