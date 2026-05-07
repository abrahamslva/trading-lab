#!/bin/bash

# Top 15 repositorios relevantes de ruvnet
REPOS=(
    "ruflo"                        # IA Agents orchestration (45k stars)
    "SAFLA"                        # Trading feedback loop (147 stars)
    "guardrail"                    # Data analysis + AI (149 stars)
    "FACT"                         # Context augmentation tools (165 stars)
    "Bot-Generator-Bot"            # Trading bot generator (565 stars)
    "QuDAG"                        # AI + Trading protocol (167 stars)
    "agentic-flow"                 # AI model switching (682 stars)
    "rUv-dev"                      # AI dev tools (424 stars)
    "RuVector"                     # Neural network library (3.9k stars)
    "SynthLang"                    # Efficient prompt lang (253 stars)
    "dspy.ts"                      # Declarative AI JS (245 stars)
    "voicebot"                     # Voice trading bot (99 stars)
    "GenAI-Superstream"            # Agentic data engineering (57 stars)
    "hello_world_agent"            # Agent example (99 stars)
    "ruvbot"                       # Trading bot assistant (43 stars)
)

echo "🔄 Clonando repositorios relevantes de ruvnet..."
echo "================================================"

for repo in "${REPOS[@]}"; do
    echo ""
    echo "📦 Clonando: $repo"
    git clone --depth 1 https://github.com/ruvnet/$repo.git $repo 2>&1 | tail -3
    if [ -d "$repo" ]; then
        echo "  ✓ Éxito"
    else
        echo "  ✗ Error"
    fi
done

echo ""
echo "================================================"
echo "✓ Clonado completo"
ls -la --group-directories-first | grep "^d" | tail -20

