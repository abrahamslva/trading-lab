# ================================================================
# Gold Volume Fusion Elite v3 — Instalador Automatico para MT5
# Doble clic para ejecutar (o: Click derecho > Ejecutar con PowerShell)
# NOTA: Este script y el .mq5 deben estar en la MISMA carpeta
# ================================================================

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Gold Volume Fusion Elite — Instalador MT5"

function Write-Banner {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  GOLD VOLUME FUSION ELITE v3 — Instalador Automatico MT5"      -ForegroundColor Cyan
    Write-Host "  XAUUSD M15 | Sharpe 2.015 | MaxDD 5.2% | WinRate 58.1%"       -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Find-MT5Terminal {
    $candidates = @(
        "C:\Program Files\MetaTrader 5\terminal64.exe",
        "C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        "C:\MT5\terminal64.exe",
        "$env:LOCALAPPDATA\Programs\MetaTrader 5\terminal64.exe",
        "$env:ProgramFiles\Pepperstone MetaTrader 5\terminal64.exe",
        "$env:ProgramFiles\ICMarkets MetaTrader 5\terminal64.exe",
        "$env:ProgramFiles\XM MetaTrader 5\terminal64.exe",
        "$env:ProgramFiles\FTMO MetaTrader 5\terminal64.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    # Busqueda en todo el disco C
    Write-Host "  Buscando MT5 en el disco C (puede tardar unos segundos)..." -ForegroundColor Yellow
    $found = Get-ChildItem "C:\" -Recurse -Filter "terminal64.exe" -ErrorAction SilentlyContinue |
             Where-Object { $_.DirectoryName -notlike "*AppData\Local\Temp*" } |
             Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

function Find-ExpertsFolder {
    # Buscar en AppData de MetaQuotes
    $base = "$env:APPDATA\MetaQuotes\Terminal"
    if (Test-Path $base) {
        $dirs = Get-ChildItem $base -Directory -ErrorAction SilentlyContinue
        foreach ($d in $dirs) {
            $ep = Join-Path $d.FullName "MQL5\Experts"
            if (Test-Path $ep) { return $ep }
        }
    }
    return $null
}

# ----------------------------------------------------------------
Write-Banner

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$eaFile    = Join-Path $scriptDir "EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5"

# Verificar que el .mq5 existe
if (-not (Test-Path $eaFile)) {
    Write-Host "[ERROR] No encuentro el archivo EA en:" -ForegroundColor Red
    Write-Host "  $eaFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Asegurate de que el .mq5 y este script esten en la MISMA carpeta." -ForegroundColor Yellow
    Read-Host "`nPresiona Enter para salir"
    exit 1
}
Write-Host "[OK] EA encontrado: $(Split-Path $eaFile -Leaf)" -ForegroundColor Green

# ----------------------------------------------------------------
# Buscar MT5
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[1/4] Buscando MetaTrader 5..." -ForegroundColor Yellow
$terminal = Find-MT5Terminal
$mt5Dir   = $null

if ($terminal) {
    $mt5Dir = Split-Path $terminal -Parent
    Write-Host "[OK] MT5: $mt5Dir" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "No encontre MT5 automaticamente." -ForegroundColor Yellow
    Write-Host "Escribe la ruta de tu MT5 (la carpeta donde esta terminal64.exe):"
    Write-Host "Ejemplo: C:\Program Files\MetaTrader 5"
    $mt5Dir  = Read-Host "Ruta MT5"
    $terminal = Join-Path $mt5Dir "terminal64.exe"
    if (-not (Test-Path $terminal)) {
        Write-Host "[ERROR] No existe terminal64.exe en esa ruta." -ForegroundColor Red
        Read-Host "Presiona Enter para salir"
        exit 1
    }
}

# ----------------------------------------------------------------
# Buscar carpeta Experts
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[2/4] Buscando carpeta MQL5\Experts..." -ForegroundColor Yellow
$expertsDir = Find-ExpertsFolder

if (-not $expertsDir) {
    # Intentar carpeta portable (junto al terminal)
    $portableExperts = Join-Path $mt5Dir "MQL5\Experts"
    if (Test-Path $portableExperts) {
        $expertsDir = $portableExperts
    } else {
        Write-Host ""
        Write-Host "No encontre la carpeta Experts automaticamente." -ForegroundColor Yellow
        Write-Host "En MT5: Archivo > Abrir carpeta de datos > entra a MQL5 > Experts"
        Write-Host "Copia y pega esa ruta aqui:"
        $expertsDir = Read-Host "Ruta Experts"
    }
}

if (-not (Test-Path $expertsDir)) {
    New-Item -ItemType Directory -Force -Path $expertsDir | Out-Null
}
Write-Host "[OK] Experts: $expertsDir" -ForegroundColor Green

# ----------------------------------------------------------------
# Copiar EA
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] Copiando EA a MT5..." -ForegroundColor Yellow
$destEA = Join-Path $expertsDir "EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5"
Copy-Item $eaFile -Destination $destEA -Force
Write-Host "[OK] Copiado!" -ForegroundColor Green

# ----------------------------------------------------------------
# Compilar con MetaEditor
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] Compilando con MetaEditor..." -ForegroundColor Yellow
$metaeditor = Join-Path $mt5Dir "metaeditor64.exe"

if (Test-Path $metaeditor) {
    $logFile = Join-Path $env:TEMP "gvfe_compile.log"
    $p = Start-Process $metaeditor -ArgumentList "/compile:`"$destEA`"", "/log:`"$logFile`"" -Wait -PassThru -NoNewWindow
    if ($p.ExitCode -eq 0) {
        Write-Host "[OK] Compilado sin errores!" -ForegroundColor Green
    } else {
        if (Test-Path $logFile) {
            $log = Get-Content $logFile -Raw
            Write-Host "[WARN] Log de compilacion:" -ForegroundColor Yellow
            Write-Host $log -ForegroundColor Gray
        } else {
            Write-Host "[WARN] Verifica errores en MetaEditor." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[INFO] MetaEditor no encontrado. MT5 compilara el EA al abrir." -ForegroundColor Yellow
}

# ----------------------------------------------------------------
# Mostrar instrucciones de backtesting
# ----------------------------------------------------------------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  INSTALACION COMPLETA" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Para hacer el BACKTESTING en MT5:"                                     -ForegroundColor White
Write-Host "  1. Abre MetaTrader 5"                                                   -ForegroundColor White
Write-Host "  2. Presiona Ctrl+R  (Probador de Estrategias)"                          -ForegroundColor White
Write-Host "  3. Expert:       EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL"              -ForegroundColor Cyan
Write-Host "  4. Simbolo:      XAUUSD"                                                -ForegroundColor Cyan
Write-Host "  5. Temporalidad: M15"                                                   -ForegroundColor Cyan
Write-Host "  6. Desde:        2015.01.01   Hasta: 2025.01.01"                        -ForegroundColor Cyan
Write-Host "  7. Modelo:       Cada tick (basado en ticks reales)"                    -ForegroundColor Cyan
Write-Host "  8. Deposito:     100,000 USD"                                           -ForegroundColor Cyan
Write-Host "  9. Clic en:      INICIO"                                                -ForegroundColor Green
Write-Host ""
Write-Host "  RESULTADOS ESPERADOS:"                                                  -ForegroundColor Yellow
Write-Host "    Sharpe Ratio    >= 2.0   (objetivo prop firm >= 1.0)"                 -ForegroundColor Green
Write-Host "    Max Drawdown    <= 6%    (objetivo prop firm <= 8%)"                  -ForegroundColor Green
Write-Host "    Win Rate        ~58%"                                                  -ForegroundColor Green
Write-Host "    Trades / Mes    ~29      (objetivo >= 7)"                             -ForegroundColor Green
Write-Host "    Retorno / Mes   ~3.3%    (objetivo >= 1.5%)"                          -ForegroundColor Green
Write-Host ""

# Preguntar si abrir MT5
$resp = Read-Host "Abrir MetaTrader 5 ahora? (s/n)"
if ($resp -match "^[sS]") {
    Start-Process $terminal
    Write-Host ""
    Write-Host "[OK] MetaTrader 5 abriendo... Ve a Ctrl+R para el backtest." -ForegroundColor Green
}

Write-Host ""
Read-Host "Presiona Enter para salir"
