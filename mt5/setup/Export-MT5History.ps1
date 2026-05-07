# mt5/Export-MT5History.ps1
# ===========================================================
# Exporta histórico XAUUSD M15 desde MetaTrader 5
# y luego convierte el CSV a parquet.
#
# Uso (PowerShell en Windows):
#   cd C:\ruta\trading-lab
#   .\mt5\Export-MT5History.ps1
#
# Requisitos:
#   - MT5 abierto y logueado
#   - Python con pandas + pyarrow:  pip install pandas pyarrow
# ===========================================================

$ErrorActionPreference = "Stop"

Write-Host "=" * 60
Write-Host "  MT5 Exportador de Historia — XAUUSD M15"
Write-Host "=" * 60

# ── 1. Localizar la carpeta de datos de MT5 ─────────────────
$MT5DataFolders = @(
    "$env:APPDATA\MetaQuotes\Terminal",
    "$env:USERPROFILE\AppData\Roaming\MetaQuotes\Terminal"
)

$HistoryRoot = $null
foreach ($base in $MT5DataFolders) {
    if (Test-Path $base) {
        # Buscar carpetas de terminales (GUID)
        $terminals = Get-ChildItem -Path $base -Directory -ErrorAction SilentlyContinue
        foreach ($t in $terminals) {
            $h = Join-Path $t.FullName "bases"
            if (Test-Path $h) {
                $HistoryRoot = $h
                Write-Host "  Terminal MT5 encontrado: $($t.FullName)"
                break
            }
        }
    }
    if ($HistoryRoot) { break }
}

if (-not $HistoryRoot) {
    Write-Host ""
    Write-Host "  MT5 no encontrado en APPDATA." -ForegroundColor Yellow
    Write-Host "  Exporta manualmente con: Herramientas → Centro de Historia → XAUUSD M15 → Exportar"
    Write-Host ""
    Write-Host "  Luego ejecuta:"
    Write-Host "    python mt5\import_csv.py <ruta-al-csv>"
    exit 0
}

# ── 2. Buscar archivos HCC/HST de XAUUSD M15 ────────────────
Write-Host ""
Write-Host "  Buscando archivos de historia XAUUSD M15..."
$HccFiles = Get-ChildItem -Path $HistoryRoot -Recurse `
    -Include "XAUUSD15.hcc","XAUUSD15.hst","XAUUSD.M15.*" `
    -ErrorAction SilentlyContinue

if ($HccFiles) {
    Write-Host "  Archivos HCC/HST encontrados:"
    $HccFiles | ForEach-Object { Write-Host "    $($_.FullName)  ($([math]::Round($_.Length/1MB, 2)) MB)" }
    Write-Host ""
    Write-Host "  NOTA: Los archivos .hcc/.hst son binarios de MT5." -ForegroundColor Cyan
    Write-Host "  Para exportar como CSV: MT5 → Ctrl+H → XAUUSD → M15 → Exportar"
}

# ── 3. Instrucciones de exportación manual ──────────────────
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════╗"
Write-Host "  ║  PASOS PARA EXPORTAR DESDE MT5:             ║"
Write-Host "  ║                                              ║"
Write-Host "  ║  1. MT5 → Herramientas → Centro de Historia ║"
Write-Host "  ║     [O presiona Ctrl+H]                     ║"
Write-Host "  ║                                              ║"
Write-Host "  ║  2. Panel izquierdo:                        ║"
Write-Host "  ║     XAUUSD → M15                            ║"
Write-Host "  ║                                              ║"
Write-Host "  ║  3. Clic derecho → 'Exportar Barras'        ║"
Write-Host "  ║                                              ║"
Write-Host "  ║  4. Guardar como: XAUUSD_M15.csv            ║"
Write-Host "  ║     en la raíz del repo trading-lab\        ║"
Write-Host "  ╚══════════════════════════════════════════════╝"
Write-Host ""

# ── 4. Esperar a que aparezca el CSV ────────────────────────
$CsvTargets = @(
    "XAUUSD_M15.csv",
    "XAUUSD15.csv",
    "XAUUSD.csv"
)
$CsvFound = $null

Write-Host "  Esperando que exportes el CSV..." -NoNewline
$timeout = 300  # segundos
$elapsed = 0
while ($elapsed -lt $timeout) {
    foreach ($name in $CsvTargets) {
        if (Test-Path $name) {
            $CsvFound = $name
            break
        }
        # También buscar en Desktop y Downloads
        $desktop  = Join-Path $env:USERPROFILE "Desktop\$name"
        $downloads = Join-Path $env:USERPROFILE "Downloads\$name"
        if (Test-Path $desktop)   { $CsvFound = $desktop;  break }
        if (Test-Path $downloads) { $CsvFound = $downloads; break }
    }
    if ($CsvFound) { break }
    Start-Sleep 3
    $elapsed += 3
    Write-Host "." -NoNewline
}

if (-not $CsvFound) {
    Write-Host ""
    Write-Host ""
    Write-Host "  Tiempo de espera agotado. Si ya tienes el CSV, ejecuta:" -ForegroundColor Yellow
    Write-Host "    python mt5\import_csv.py <ruta-al-csv>"
    exit 0
}

Write-Host ""
Write-Host "  CSV detectado: $CsvFound  ($([math]::Round((Get-Item $CsvFound).Length/1KB)) KB)"

# ── 5. Convertir CSV → Parquet ──────────────────────────────
Write-Host ""
Write-Host "  Convirtiendo CSV → Parquet..."
$pythonCmd = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }

& $pythonCmd mt5\import_csv.py $CsvFound
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR en la conversión." -ForegroundColor Red
    exit 1
}

# ── 6. Subir al Codespace si gh está disponible ─────────────
$ParquetFile = "data\dukascopy\XAUUSD_15min_mt5.parquet"
if (Test-Path $ParquetFile) {
    Write-Host ""
    Write-Host "  Parquet creado: $ParquetFile"
    $sizeMB = [math]::Round((Get-Item $ParquetFile).Length/1MB, 2)
    Write-Host "  Tamaño: $sizeMB MB"
    Write-Host ""

    if (Get-Command gh -ErrorAction SilentlyContinue) {
        Write-Host "  gh CLI detectado — subiendo al Codespace..." -ForegroundColor Cyan
        Write-Host "  (Selecciona tu Codespace si te pregunta)"
        gh codespace cp $ParquetFile `
            "remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet"

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "  ✓ Parquet subido al Codespace exitosamente!" -ForegroundColor Green
            Write-Host "  El watcher detectará los datos y lanzará el backtest automáticamente."
        } else {
            Write-Host "  ⚠ Error al subir — sube manualmente:" -ForegroundColor Yellow
            Write-Host "    gh codespace cp $ParquetFile remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet"
        }
    } else {
        Write-Host "  gh CLI no encontrado. Sube el parquet manualmente:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  OPCIÓN A — Instalar gh CLI y ejecutar:"
        Write-Host "    winget install GitHub.cli"
        Write-Host "    gh auth login"
        Write-Host "    gh codespace cp $ParquetFile remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet"
        Write-Host ""
        Write-Host "  OPCIÓN B — VS Code:"
        Write-Host "    Abre VS Code → conecta al Codespace → arrastra el parquet al explorador"
        Write-Host ""
        Write-Host "  OPCIÓN C — scp (si tienes SSH configurado):"
        Write-Host "    scp $ParquetFile <user>@<codespace-host>:/workspaces/trading-lab/data/dukascopy/"
    }
}

Write-Host ""
Write-Host "=" * 60
Write-Host "  LISTO"
Write-Host "=" * 60
