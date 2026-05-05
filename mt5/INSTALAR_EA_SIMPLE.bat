@echo off
title Instalador EA Gold Volume Fusion Elite

echo.
echo ================================================================
echo   INSTALADOR EA - Gold Volume Fusion Elite v3
echo ================================================================
echo.

:: ====================================================
:: PASO 1: Encontrar donde esta el .mq5
:: ====================================================
set "SCRIPT_DIR=%~dp0"
set "EA_MQ5=%SCRIPT_DIR%EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5"

if not exist "%EA_MQ5%" (
    echo ERROR: No encuentro el archivo EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5
    echo Asegurate de que el .bat y el .mq5 esten en la MISMA carpeta.
    echo.
    pause
    exit /b
)

echo Archivo EA encontrado: %EA_MQ5%
echo.

:: ====================================================
:: PASO 2: Buscar la carpeta Experts de MT5
:: ====================================================
set "EXPERTS="

:: Buscar en AppData (lugar mas comun)
for /d %%D in ("%APPDATA%\MetaQuotes\Terminal\*") do (
    if exist "%%D\MQL5\Experts" (
        set "EXPERTS=%%D\MQL5\Experts"
    )
)

:: Si no encontro, buscar instalacion portable
if "%EXPERTS%"=="" (
    for %%P in (
        "C:\Program Files\MetaTrader 5\MQL5\Experts"
        "C:\Program Files (x86)\MetaTrader 5\MQL5\Experts"
        "C:\MT5\MQL5\Experts"
        "%USERPROFILE%\Desktop\MetaTrader 5\MQL5\Experts"
        "%USERPROFILE%\Downloads\MetaTrader 5\MQL5\Experts"
    ) do (
        if exist "%%~P" set "EXPERTS=%%~P"
    )
)

if "%EXPERTS%"=="" (
    echo No encontre la carpeta Experts de MT5 automaticamente.
    echo.
    echo Ingresa la ruta completa de tu carpeta MQL5\Experts:
    echo Ejemplo: C:\Program Files\MetaTrader 5\MQL5\Experts
    echo.
    set /p "EXPERTS=Ruta: "
)

if not exist "%EXPERTS%" (
    echo Creando carpeta: %EXPERTS%
    mkdir "%EXPERTS%"
)

echo Carpeta Experts: %EXPERTS%
echo.

:: ====================================================
:: PASO 3: Copiar el EA
:: ====================================================
echo Copiando EA...
copy /Y "%EA_MQ5%" "%EXPERTS%\" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR al copiar. Intenta cerrar MetaTrader 5 primero.
    pause
    exit /b
)
echo [OK] EA copiado a: %EXPERTS%\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5
echo.

:: ====================================================
:: PASO 4: Buscar MetaEditor para compilar
:: ====================================================
set "EDITOR="
for %%P in (
    "C:\Program Files\MetaTrader 5\metaeditor64.exe"
    "C:\Program Files (x86)\MetaTrader 5\metaeditor64.exe"
    "C:\MT5\metaeditor64.exe"
) do (
    if exist "%%~P" set "EDITOR=%%~P"
)

if not "%EDITOR%"=="" (
    echo Compilando con MetaEditor...
    "%EDITOR%" /compile:"%EXPERTS%\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5"
    echo [OK] Compilado!
    echo.
) else (
    echo MetaEditor no encontrado - MT5 compilara al iniciar.
    echo.
)

:: ====================================================
:: PASO 5: Buscar terminal64.exe para abrir MT5
:: ====================================================
set "TERMINAL="
for %%P in (
    "C:\Program Files\MetaTrader 5\terminal64.exe"
    "C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
    "C:\MT5\terminal64.exe"
) do (
    if exist "%%~P" set "TERMINAL=%%~P"
)

echo ================================================================
echo.
echo   EA instalado correctamente!
echo.
echo   Siguientes pasos en MetaTrader 5:
echo.
echo   1. Abre MetaTrader 5
echo   2. Presiona Ctrl+R  (Probador de Estrategias)
echo   3. Expert: EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL
echo   4. Simbolo: XAUUSD
echo   5. Temporalidad: M15
echo   6. Desde 2015.01.01  hasta  2025.01.01
echo   7. Modelo: Cada tick
echo   8. Deposito: 100000
echo   9. Clic en INICIO
echo.
echo ================================================================
echo.

if not "%TERMINAL%"=="" (
    set /p "ABRIR=Abrir MetaTrader 5 ahora? (s/n): "
    if /i "%ABRIR%"=="s" (
        start "" "%TERMINAL%"
        echo MetaTrader 5 abriendo...
    )
) else (
    echo Abre MetaTrader 5 manualmente.
)

echo.
pause
