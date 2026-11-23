@echo off
chcp 65001 >nul
title BASTIUM
cd /d "%~dp0"

rem --- 1. Entorno virtual: se crea solo si no existe ---
if not exist ".venv\Scripts\python.exe" (
    echo Primera ejecucion: creando entorno virtual...
    where py >nul 2>nul
    if not errorlevel 1 (
        rem Version recomendada: Python 3.15 ^(Sprint 122^); si no esta, la mas nueva instalada.
        py -3.15 -m venv .venv >nul 2>nul
        if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if not exist ".venv\Scripts\python.exe" (
        echo.
        echo ============================================================
        echo   No se pudo crear el entorno virtual.
        echo   Verifica que Python 3 este instalado y en el PATH
        echo   ^(https://www.python.org/downloads/^).
        echo ============================================================
        echo.
        pause
        exit /b 1
    )
)

rem --- 2. Dependencias: se instalan si falta alguna de las criticas ---
".venv\Scripts\python.exe" -c "import PySide6, sqlalchemy, docx, reportlab, rich, matplotlib, holidays" >nul 2>nul
if errorlevel 1 (
    echo Instalando dependencias ^(puede tardar unos minutos^)...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo   No se pudieron instalar las dependencias.
        echo   Revisa tu conexion a internet y vuelve a intentarlo.
        echo   Si el error menciona PySide6, borra la carpeta .venv y
        echo   vuelve a abrir este archivo con Python 3.15 o 3.13 instalado.
        echo ============================================================
        echo.
        pause
        exit /b 1
    )
)

rem --- 3. Arranque ---
".venv\Scripts\python.exe" main.py

if not "%errorlevel%"=="0" (
    echo.
    echo ============================================================
    echo   BASTIUM se cerro con un error inesperado.
    echo.
    echo   Copia el mensaje de error que aparece arriba y compartelo
    echo   con la persona encargada de soporte del programa.
    echo ============================================================
    echo.
    pause
    exit /b 1
)
