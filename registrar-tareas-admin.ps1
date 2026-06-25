# Ejecutar este archivo como Administrador
# Click derecho → "Ejecutar con PowerShell" o desde terminal admin

Write-Host "`n  Registrando tareas en el Task Scheduler...`n" -ForegroundColor Cyan

# ── Tarea 1: MisTools Server al iniciar sesion ──────────────
$action1 = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "app.py" `
    -WorkingDirectory "F:\Downloads\SCRIPTS CLAUDE\MisTools"

$trigger1 = New-ScheduledTaskTrigger -AtLogOn

$settings1 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit 0 `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "MisTools Server" `
    -TaskPath "\MisTools\" `
    -Action $action1 `
    -Trigger $trigger1 `
    -Settings $settings1 `
    -RunLevel Highest `
    -Description "Inicia el servidor local de MisTools en localhost:7777 al iniciar sesion" `
    -Force | Out-Null

Write-Host "  [OK] MisTools Server — arranca con Windows en localhost:7777" -ForegroundColor Green

# ── Tarea 2: ClaudeCleaner diario a las 10am ────────────────
$action2 = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -NonInteractive -WindowStyle Hidden -File `"F:\Downloads\SCRIPTS CLAUDE\MisTools\scripts\ClaudeCleanerWeb.ps1`""

$trigger2 = New-ScheduledTaskTrigger -Daily -At "10:00AM"

$settings2 = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

Register-ScheduledTask `
    -TaskName "ClaudeCleaner Diario" `
    -TaskPath "\MisTools\" `
    -Action $action2 `
    -Trigger $trigger2 `
    -Settings $settings2 `
    -RunLevel Highest `
    -Description "Limpieza automatica diaria de temp, cache y papelera" `
    -Force | Out-Null

Write-Host "  [OK] ClaudeCleaner Diario — corre todos los dias a las 10:00am" -ForegroundColor Green

# ── Verificacion ─────────────────────────────────────────────
Write-Host "`n  Tareas registradas:`n" -ForegroundColor Cyan
Get-ScheduledTask -TaskPath "\MisTools\" | ForEach-Object {
    $info = Get-ScheduledTaskInfo $_.TaskName -TaskPath $_.TaskPath -ErrorAction SilentlyContinue
    Write-Host "  - $($_.TaskName)" -ForegroundColor White
    if ($info.NextRunTime) { Write-Host "    Proxima ejecucion: $($info.NextRunTime)" -ForegroundColor DarkGray }
}

Write-Host "`n  Listo. Puedes cerrar esta ventana.`n" -ForegroundColor Cyan
Read-Host "  Presiona Enter para cerrar"
