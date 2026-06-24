@echo off
title MisTools
color 0A
echo.
echo  ==========================================
echo   MisTools - Iniciando servidor local...
echo  ==========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado en PATH.
    echo  Descargalo en: https://www.python.org/downloads/
    echo  Activa "Add Python to PATH" al instalar.
    pause
    exit /b 1
)

echo  Python encontrado. Verificando Flask...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo  Instalando Flask por primera vez, espera...
    pip install flask -q
    if errorlevel 1 (
        echo  [ERROR] No se pudo instalar Flask.
        pause
        exit /b 1
    )
)

echo  Flask OK.
echo.
echo  Servidor corriendo en: http://localhost:7777
echo  Abriendo browser automaticamente...
echo.
echo  Para cerrar la app: cierra esta ventana o Ctrl+C
echo  ==========================================
echo.

cd /d "%~dp0"
python app.py

echo.
echo  Servidor detenido.
pause
