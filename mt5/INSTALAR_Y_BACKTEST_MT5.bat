@echo off
setlocal EnableDelayedExpansion
title Gold Volume Fusion Elite — Instalador y Backtesting MT5

echo.
echo ================================================================
echo   GOLD VOLUME FUSION ELITE v3 — Instalador Automatico MT5
echo   Backtesting: XAUUSD M15 ^| 10 anios ^| Prop Firm Ready
echo ================================================================
echo.

:: ----------------------------------------------------------------
:: 1. Detectar la carpeta de instalacion de MetaTrader 5
:: ----------------------------------------------------------------
set "MT5_PATH="
set "MT5_DATA="

:: Buscar en rutas comunes de MT5
for %%P in (
    "C:\Program Files\MetaTrader 5"
    "C:\Program Files (x86)\MetaTrader 5"
    "%APPDATA%\MetaTrader 5"
    "C:\MT5"
) do (
    if exist "%%~P\terminal64.exe" (
        set "MT5_PATH=%%~P"
        goto :found_mt5
    )
)

:: Buscar en el registro de Windows
for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\MetaQuotes Software Corp\MetaTrader 5" /v "ExePath" 2^>nul') do (
    set "MT5_PATH=%%B"
    goto :found_mt5
)

echo [ERROR] No se encontro MetaTrader 5.
echo Instala MT5 desde: https://www.metatrader5.com/es/download
echo O edita este script con tu ruta de MT5 en la variable MT5_PATH
pause
exit /b 1

:found_mt5
echo [OK] MetaTrader 5 encontrado en: %MT5_PATH%

:: Detectar carpeta de datos (AppData)
for /f "delims=" %%A in ('"%MT5_PATH%\terminal64.exe" /help 2^>nul ^| find "Data"') do set "MT5_DATA_LINE=%%A"

:: Ruta estandar de datos MT5
set "MT5_DATA=%APPDATA%\MetaQuotes\Terminal"

:: Buscar la carpeta de datos real
for /d %%D in ("%APPDATA%\MetaQuotes\Terminal\*") do (
    if exist "%%D\MQL5\Experts" (
        set "MT5_DATA=%%D"
        goto :found_data
    )
)

:found_data
set "EXPERTS_DIR=%MT5_DATA%\MQL5\Experts"
set "RESULTS_DIR=%MT5_DATA%\MQL5\Files"
echo [OK] Carpeta de Experts: %EXPERTS_DIR%

:: ----------------------------------------------------------------
:: 2. Obtener la carpeta donde esta este script (los archivos del EA)
:: ----------------------------------------------------------------
set "SCRIPT_DIR=%~dp0"
set "EA_FILE=%SCRIPT_DIR%EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5"
set "INI_FILE=%SCRIPT_DIR%backtest_config.ini"

if not exist "%EA_FILE%" (
    echo.
    echo [ERROR] No se encuentra el archivo EA:
    echo   %EA_FILE%
    echo.
    echo Asegurate de que este .bat este en la misma carpeta que el .mq5
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: 3. Copiar el EA a la carpeta de MT5
:: ----------------------------------------------------------------
echo.
echo [PASO 1] Copiando EA a MT5...
if not exist "%EXPERTS_DIR%" mkdir "%EXPERTS_DIR%"
copy /Y "%EA_FILE%" "%EXPERTS_DIR%\" >nul
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo copiar el EA. MT5 puede estar bloqueando el archivo.
    echo Cierra MetaTrader 5 e intenta de nuevo.
    pause
    exit /b 1
)
echo [OK] EA copiado: %EXPERTS_DIR%\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5

:: ----------------------------------------------------------------
:: 4. Copiar el archivo INI de configuracion del backtest
:: ----------------------------------------------------------------
echo.
echo [PASO 2] Copiando configuracion de backtesting...
copy /Y "%INI_FILE%" "%MT5_PATH%\backtest_config.ini" >nul 2>&1
if %errorlevel% neq 0 (
    copy /Y "%INI_FILE%" "%SCRIPT_DIR%backtest_config_local.ini" >nul
    set "INI_FILE=%SCRIPT_DIR%backtest_config_local.ini"
)
echo [OK] Configuracion lista

:: ----------------------------------------------------------------
:: 5. Compilar el EA con MetaEditor (automatico)
:: ----------------------------------------------------------------
echo.
echo [PASO 3] Compilando EA con MetaEditor 64...
set "METAEDITOR=%MT5_PATH%\metaeditor64.exe"

if not exist "%METAEDITOR%" (
    echo [WARN] MetaEditor no encontrado en %METAEDITOR%
    echo La compilacion se hara automaticamente cuando MT5 inicie.
    goto :run_backtest
)

"%METAEDITOR%" /compile:"%EXPERTS_DIR%\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5" /log
if %errorlevel% neq 0 (
    echo [WARN] Posible error de compilacion. Verificar en MetaEditor.
    echo Continuando de todas formas...
) else (
    echo [OK] Compilacion exitosa!
)

:: ----------------------------------------------------------------
:: 6. Crear carpeta de resultados
:: ----------------------------------------------------------------
if not exist "%~dp0results" mkdir "%~dp0results"

:: ----------------------------------------------------------------
:: 7. Preguntar si ejecutar backtest automatico
:: ----------------------------------------------------------------
:run_backtest
echo.
echo ================================================================
echo   OPCIONES DE EJECUCION
echo ================================================================
echo.
echo   [1] Abrir MT5 y lanzar backtest AUTOMATICAMENTE
echo       (XAUUSD M15, 2015-2025, Every Tick, $100k)
echo.
echo   [2] Solo abrir MetaTrader 5 (backtest manual)
echo.
echo   [3] Solo compilar / instalar (no abrir MT5)
echo.
set /p "OPCION=Elige una opcion (1/2/3): "

if "%OPCION%"=="3" goto :done

if "%OPCION%"=="2" (
    echo.
    echo Abriendo MetaTrader 5...
    start "" "%MT5_PATH%\terminal64.exe"
    echo.
    echo Para hacer el backtest manual:
    echo   1. Ve a Ver ^> Probador de Estrategias (Ctrl+R)
    echo   2. Selecciona Expert: EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL
    echo   3. Simbolo: XAUUSD ^| Timeframe: M15
    echo   4. Desde: 2015.01.01 hasta 2025.01.01
    echo   5. Modelo: Cada tick ^| Deposito: 100000
    echo   6. Haz clic en INICIO
    goto :done
)

:: Opcion 1: Backtest automatico con config INI
echo.
echo [PASO 4] Lanzando MT5 con backtest automatico...
echo Esto puede tardar varios minutos (10 anios de datos Every Tick)
echo.

:: Cerrar MT5 si esta abierto
taskkill /IM terminal64.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

:: Lanzar MT5 con el config de backtest
start "" "%MT5_PATH%\terminal64.exe" /config:"%MT5_PATH%\backtest_config.ini"

echo [OK] MetaTrader 5 iniciando con backtesting automatico...
echo.
echo El reporte se guardara en:
echo   %MT5_DATA%\reports\MT5_BacktestReport_XAUUSD_M15.html
echo.
echo RESULTADOS ESPERADOS (segun Python backtesting):
echo   Sharpe:       2.015  (objetivo ^>= 1.0)
echo   Max Drawdown: 5.17%%  (objetivo ^<= 8%%)
echo   Win Rate:     58.1%%
echo   Trades/Mes:   29     (objetivo ^>= 7)
echo   Retorno/Mes:  3.27%% (objetivo ^>= 1.5%%)
echo.

:done
echo.
echo ================================================================
echo   Archivos instalados correctamente.
echo ================================================================
echo.
echo   EA instalado en:
echo     %EXPERTS_DIR%\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5
echo.
echo   Para ver el EA en MT5:
echo     Navigator (Ctrl+N) ^> Expert Advisors ^> EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL
echo.
echo   Para backtest manual:
echo     Ver ^> Probador de Estrategias (Ctrl+R)
echo.
pause
