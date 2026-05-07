#!/bin/bash

echo "🔍 CLONANDO 4 REPOS ADICIONALES..."
echo "=================================="

ADDITIONAL_REPOS=(
    "https://github.com/public-apis/public-apis public-apis"
    "https://github.com/chrisworsey55/atlas-gic atlas-gic"
    "https://github.com/msitarzewski/agency-agents agency-agents"
    "https://github.com/D4Vinci/Scrapling scrapling"
)

for repo_url in "${ADDITIONAL_REPOS[@]}"; do
    repo_name=$(echo $repo_url | awk '{print $2}')
    echo ""
    echo "📦 Clonando: $repo_name"
    git clone --depth 1 $repo_url $repo_name 2>&1 | tail -5
done

echo ""
echo "✅ Clonación completada"
du -sh *
