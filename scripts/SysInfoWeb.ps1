param([string]$Sections = "os,cpu,ram,gpu,disk,net,procs")

$sel = $Sections -split ","
function Has($s) { return $sel -contains $s }

Write-Output "START|$(Get-Date -Format 'HH:mm:ss')"

if (Has "os") {
    $os = Get-CimInstance Win32_OperatingSystem
    $up = (Get-Date) - $os.LastBootUpTime
    Write-Output "OS|$($os.Caption)|Build $($os.BuildNumber)|$($os.OSArchitecture)"
    Write-Output "UPTIME|$($up.Days)d $($up.Hours)h $($up.Minutes)m|Ultimo arranque: $($os.LastBootUpTime.ToString('dd/MM/yyyy HH:mm'))"
}

if (Has "cpu") {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    Write-Output "CPU|$($cpu.Name.Trim())|$($cpu.NumberOfCores) nucleos / $($cpu.NumberOfLogicalProcessors) hilos|$($cpu.MaxClockSpeed) MHz"
    Write-Output "CPU_LOAD|$($cpu.LoadPercentage)"
}

if (Has "ram") {
    $os2 = Get-CimInstance Win32_OperatingSystem
    $tot = [math]::Round($os2.TotalVisibleMemorySize/1KB)
    $free= [math]::Round($os2.FreePhysicalMemory/1KB)
    $used= $tot - $free
    $pct = [math]::Round(($used/$tot)*100)
    Write-Output "RAM|$tot MB total|$used MB usado|$free MB libre|$pct%"
}

if (Has "gpu") {
    Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | ForEach-Object {
        $vram = if ($_.AdapterRAM -gt 0) { "$([math]::Round($_.AdapterRAM/1GB,1)) GB VRAM" } else { "VRAM desconocida" }
        Write-Output "GPU|$($_.Name.Trim())|$vram|Driver $($_.DriverVersion)"
    }
}

if (Has "disk") {
    Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.Used -ne $null -and ($_.Used + $_.Free) -gt 0) {
            $t = [math]::Round(($_.Used+$_.Free)/1GB,1)
            $u = [math]::Round($_.Used/1GB,1)
            $f = [math]::Round($_.Free/1GB,1)
            $p = [math]::Round(($_.Used/($_.Used+$_.Free))*100)
            Write-Output "DISK|$($_.Name):|$t GB|$u GB usado|$f GB libre|$p%"
        }
    }
}

if (Has "net") {
    Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Up' } | ForEach-Object {
        Write-Output "NET|$($_.Name)|$($_.InterfaceDescription)|$($_.LinkSpeed)"
    }
    try {
        $ip = (Invoke-WebRequest -Uri 'https://api.ipify.org' -TimeoutSec 3 -UseBasicParsing).Content
        Write-Output "IP_PUBLIC|$ip"
    } catch { Write-Output "IP_PUBLIC|No disponible" }
}

if (Has "procs") {
    Write-Output "INFO|Top procesos por uso de CPU:"
    Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 | ForEach-Object {
        $mem = [math]::Round($_.WorkingSet64/1MB)
        Write-Output "PROC|$($_.ProcessName)|CPU $([math]::Round($_.CPU,1))s|RAM $mem MB"
    }
}

Write-Output "END|OK"
