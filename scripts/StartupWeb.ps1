param([string]$Filter = "all")

Write-Output "START|$(Get-Date -Format 'HH:mm:ss')"
Write-Output "INFO|Leyendo entradas de inicio ($Filter)..."

$count = 0

if ($Filter -eq "all" -or $Filter -eq "user") {
    $userPaths = @(
        @{ Path = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run';     Label = 'Usuario - Run' },
        @{ Path = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce'; Label = 'Usuario - RunOnce' }
    )
    foreach ($r in $userPaths) {
        if (Test-Path $r.Path) {
            $props = Get-ItemProperty $r.Path -ErrorAction SilentlyContinue
            if ($props) {
                $props.PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' } | ForEach-Object {
                    Write-Output "ITEM|$($_.Name)|$($_.Value)|$($r.Label)"
                    $count++
                }
            }
        }
    }
    $sp = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
    if (Test-Path $sp) {
        Get-ChildItem $sp -File -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Output "ITEM|$($_.Name)|$($_.FullName)|Carpeta Startup (usuario)"
            $count++
        }
    }
}

if ($Filter -eq "all" -or $Filter -eq "system") {
    $sysPaths = @(
        @{ Path = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run';          Label = 'Sistema - Run' },
        @{ Path = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce';      Label = 'Sistema - RunOnce' },
        @{ Path = 'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run'; Label = 'Sistema - Run (32bit)' }
    )
    foreach ($r in $sysPaths) {
        if (Test-Path $r.Path) {
            $props = Get-ItemProperty $r.Path -ErrorAction SilentlyContinue
            if ($props) {
                $props.PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' } | ForEach-Object {
                    Write-Output "ITEM|$($_.Name)|$($_.Value)|$($r.Label)"
                    $count++
                }
            }
        }
    }
    $sp = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
    if (Test-Path $sp) {
        Get-ChildItem $sp -File -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Output "ITEM|$($_.Name)|$($_.FullName)|Carpeta Startup (sistema)"
            $count++
        }
    }
    Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Output "ITEM|$($_.Name)|$($_.Command)|WMI - $($_.Location)"
        $count++
    }
}

Write-Output "TOTAL_ITEMS|$count"
Write-Output "END|OK"
