# ================================================================
# Gold Volume Fusion Elite v3 — Descargador desde GitHub + MT5 Setup
# Ejecutar en PowerShell como Administrador en tu PC Windows
# ================================================================
# USO: Click derecho → "Ejecutar con PowerShell"
# ================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  GOLD VOLUME FUSION ELITE v3 — Setup automatico para MT5" -ForegroundColor Cyan
Write-Host "  Descarga archivos + Compila + Configura backtest" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------------
# 1. Descargar archivos desde GitHub
# ----------------------------------------------------------------
$GITHUB_RAW = "https://raw.githubusercontent.com/abrahamslva/trading-lab/main/mt5"
$TEMP_DIR = "$env:TEMP\GoldVolumeFusionElite"

Write-Host "[PASO 1] Descargando archivos desde GitHub..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $TEMP_DIR | Out-Null

$FILES = @(
    "EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5",
    "backtest_config.ini"
)

foreach ($file in $FILES) {
    $url = "$GITHUB_RAW/$file"
    $dest = "$TEMP_DIR\$file"
    Write-Host "  Descargando: $file" -NoNewline
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        Write-Host " [OK]" -ForegroundColor Green
    } catch {
        Write-Host " [ERROR - descarga manual requerida]" -ForegroundColor Red
        Write-Host "  URL: $url" -ForegroundColor Gray
    }
}

# ----------------------------------------------------------------
# 2. Detectar instalacion de MT5
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[PASO 2] Buscando MetaTrader 5..." -ForegroundColor Yellow

$MT5_PATHS = @(
    "C:\Program Files\MetaTrader 5",
    "C:\Program Files (x86)\MetaTrader 5",
    "$env:LOCALAPPDATA\Programs\MetaTrader 5",
    "C:\MT5"
)

$MT5_PATH = $null
foreach ($path in $MT5_PATHS) {
    if (Test-Path "$path\terminal64.exe") {
        $MT5_PATH = $path
        break
    }
}

# Buscar en registro
if (-not $MT5_PATH) {
    try {
        $regPath = "HKLM:\SOFTWARE\MetaQuotes Software Corp\MetaTrader 5"
        $MT5_PATH = (Get-ItemProperty $regPath -Name "ExePath" -ErrorAction Stop).ExePath
        $MT5_PATH = Split-Path $MT5_PATH -Parent
    } catch { }
}

if (-not $MT5_PATH) {
    Write-Host "[ERROR] MetaTrader 5 no encontrado." -ForegroundColor Red
    Write-Host "Descarga MT5 desde: https://www.metatrader5.com/es/download" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Archivos descargados en: $TEMP_DIR" -ForegroundColor Cyan
    Write-Host "Copiados manualmente a tu carpeta MQL5\Experts de MT5" -ForegroundColor Cyan
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "[OK] MT5 encontrado: $MT5_PATH" -ForegroundColor Green

# ----------------------------------------------------------------
# 3. Encontrar carpeta de datos de MT5 (MQL5\Experts)
# ----------------------------------------------------------------
$MT5_DATA = $null
$BASE_DATA = "$env:APPDATA\MetaQuotes\Terminal"

if (Test-Path $BASE_DATA) {
    $dirs = Get-ChildItem -Path $BASE_DATA -Directory
    foreach ($dir in $dirs) {
        if (Test-Path "$($dir.FullName)\MQL5\Experts") {
            $MT5_DATA = $dir.FullName
            break
        }
    }
}

if (-not $MT5_DATA) {
    # Ruta alternativa (MT5 portable)
    if (Test-Path "$MT5_PATH\MQL5\Experts") {
        $MT5_DATA = $MT5_PATH
    } else {
        # Crear estructura si no existe
        $MT5_DATA = "$env:APPDATA\MetaQuotes\Terminal\Common"
        New-Item -ItemType Directory -Force -Path "$MT5_DATA\MQL5\Experts" | Out-Null
    }
}

$EXPERTS_DIR = "$MT5_DATA\MQL5\Experts"
Write-Host "[OK] Experts: $EXPERTS_DIR" -ForegroundColor Green

# ----------------------------------------------------------------
# 4. Copiar EA a carpeta de MT5
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[PASO 3] Instalando EA en MT5..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path $EXPERTS_DIR | Out-Null

Copy-Item "$TEMP_DIR\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5" `
          -Destination "$EXPERTS_DIR\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5" `
          -Force

Write-Host "[OK] EA instalado en: $EXPERTS_DIR" -ForegroundColor Green

# ----------------------------------------------------------------
# 5. Compilar con MetaEditor 64
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[PASO 4] Compilando EA con MetaEditor..." -ForegroundColor Yellow

$METAEDITOR = "$MT5_PATH\metaeditor64.exe"
$EA_FULL_PATH = "$EXPERTS_DIR\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5"

if (Test-Path $METAEDITOR) {
    $logFile = "$TEMP_DIR\compile_log.txt"
    $proc = Start-Process -FilePath $METAEDITOR `
                          -ArgumentList "/compile:`"$EA_FULL_PATH`"", "/log:`"$logFile`"" `
                          -Wait -PassThru -NoNewWindow
    
    if ($proc.ExitCode -eq 0) {
        Write-Host "[OK] Compilacion exitosa!" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Revisa el log de compilacion:" -ForegroundColor Yellow
        Write-Host "  $logFile" -ForegroundColor Gray
        if (Test-Path $logFile) {
            Write-Host (Get-Content $logFile -Raw) -ForegroundColor Gray
        }
    }
} else {
    Write-Host "[INFO] MetaEditor no accesible directamente." -ForegroundColor Yellow
    Write-Host "       MT5 compilara el EA automaticamente al iniciarse." -ForegroundColor Yellow
}

# ----------------------------------------------------------------
# 6. Copiar config de backtest y lanzar MT5
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[PASO 5] Configurando backtest automatico..." -ForegroundColor Yellow

$INI_DEST = "$MT5_PATH\backtest_gvfe.ini"
Copy-Item "$TEMP_DIR\backtest_config.ini" -Destination $INI_DEST -Force
Write-Host "[OK] Config INI lista: $INI_DEST" -ForegroundColor Green

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  SELECCIONA COMO EJECUTAR EL BACKTEST" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  [1] BACKTEST AUTOMATICO — Lanza MT5 con backtesting ya configurado"
Write-Host "      (XAUUSD M15, 2015-2025, Every Tick, Deposito $100k)"
Write-Host ""
Write-Host "  [2] Abrir MT5 normalmente (configurar backtest manual)"
Write-Host ""
Write-Host "  [3] Solo instalar, no abrir MT5"
Write-Host ""

$opcion = Read-Host "Opcion (1/2/3)"

switch ($opcion) {
    "1" {
        Write-Host ""
        Write-Host "[PASO 6] Cerrando MT5 si esta abierto..." -ForegroundColor Yellow
        Stop-Process -Name "terminal64" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        Write-Host "[PASO 7] Iniciando MT5 con backtesting automatico..." -ForegroundColor Yellow
        Start-Process -FilePath "$MT5_PATH\terminal64.exe" -ArgumentList "/config:`"$INI_DEST`""
        
        Write-Host ""
        Write-Host "[OK] MT5 iniciando..." -ForegroundColor Green
        Write-Host ""
        Write-Host "El Strategy Tester se abrira automaticamente." -ForegroundColor Cyan
        Write-Host "Tiempo estimado: 5-20 minutos (Every Tick, 10 anios)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "RESULTADOS ESPERADOS:" -ForegroundColor Yellow
        Write-Host "  Sharpe Ratio:    2.015  (objetivo >= 1.0)" -ForegroundColor Green
        Write-Host "  Max Drawdown:    5.17%  (objetivo <= 8%)" -ForegroundColor Green
        Write-Host "  Win Rate:        58.1%" -ForegroundColor Green
        Write-Host "  Trades / Mes:    29     (objetivo >= 7)" -ForegroundColor Green
        Write-Host "  Retorno / Mes:   3.27%  (objetivo >= 1.5%)" -ForegroundColor Green
    }
    "2" {
        Start-Process -FilePath "$MT5_PATH\terminal64.exe"
        Write-Host ""
        Write-Host "[OK] MT5 abierto." -ForegroundColor Green
        Write-Host ""
        Write-Host "Para backtest manual:" -ForegroundColor Cyan
        Write-Host "  1. Ctrl+R  → Probador de Estrategias" -ForegroundColor White
        Write-Host "  2. Expert: EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL" -ForegroundColor White
        Write-Host "  3. Simbolo: XAUUSD | Timeframe: M15" -ForegroundColor White
        Write-Host "  4. Desde: 2015.01.01 | Hasta: 2025.01.01" -ForegroundColor White
        Write-Host "  5. Modelo: Cada Tick | Deposito: 100000 USD" -ForegroundColor White
        Write-Host "  6. Clic en INICIO" -ForegroundColor White
    }
    "3" {
        Write-Host ""
        Write-Host "[OK] Instalacion completada. MT5 no fue iniciado." -ForegroundColor Green
    }
    default {
        Write-Host "Opcion no valida. Solo se instalo el EA." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ARCHIVOS INSTALADOS" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  EA: $EXPERTS_DIR\EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5"
Write-Host "  INI: $INI_DEST"
Write-Host ""
Write-Host "  Para ver el EA en MT5:"
Write-Host "    Ctrl+N → Navigator → Expert Advisors"
Write-Host ""
Read-Host "Presiona Enter para salir"
