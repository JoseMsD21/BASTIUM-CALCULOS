@echo off
chcp 65001 >nul
title BASTIUM
cd /d %~dp0

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo ============================================================
    echo   No se encontro el entorno virtual de BASTIUM.
    echo.
    echo   Antes de poder abrir el programa por primera vez hace
    echo   falta instalar sus dependencias. Sigue el paso de
    echo   "Instalacion" del archivo README.md o de la Guia de
    echo   Usuario ^(docs\GUIA_USUARIO.md, seccion 2^) que vienen con
    echo   este proyecto.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

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
