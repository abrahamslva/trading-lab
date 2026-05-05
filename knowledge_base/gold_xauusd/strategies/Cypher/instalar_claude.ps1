#!/usr/bin/powershell

# Verificar Node.js/NPM
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando Node.js via Winget..."
    winget install --id nodejs --exact-version 18.17.0
}

# Instalar claude-code globalmente
npm install -g @anthropic-ai/claude-code

# Obtener API Key de OpenRouter
$apiKey = Read-Host "Ingrese su API Key de OpenRouter:"

# Configurar variables de entorno permanentes
Set-Item Env:ANTHROPIC_API_KEY $apiKey
Set-Item Env:ANTHROPIC_BASE_URL "https://openrouter.ai/api/v1"
Set-Item Env:ANTHROPIC_MODEL "meta-llama/llama-3.3-70b-instruct:free"

# Crear alias
Set-Alias claude-free "claude-code"

Write-Host "Configuración completada. Use 'claude-free' para iniciar."