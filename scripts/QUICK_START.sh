#!/bin/bash
# Quick Start Script for GitVisionCLI

echo "🚀 GitVisionCLI Quick Start"
echo "============================"
echo ""

# Check Python version
python3 --version

# Check if module can be imported
echo ""
echo "📦 Checking installation..."
python3 -c "import gitvisioncli; print('✅ GitVisionCLI module found')" 2>&1 || {
    echo "❌ Module not found. Installing..."
    pip install -e .
}

# Check API keys
echo ""
echo "🔑 Checking API keys..."
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  No API keys found. Set one:"
    echo "   export OPENAI_API_KEY='sk-...'"
    echo "   export ANTHROPIC_API_KEY='sk-ant-...'"
    echo "   export GOOGLE_API_KEY='...'"
    echo ""
    echo "   Or use Ollama (local, free):"
    echo "   brew install ollama  # macOS"
    echo "   ollama pull llama2"
else
    echo "✅ API key found"
fi

# Launch GitVisionCLI
echo ""
echo "🎮 Launching GitVisionCLI..."
echo ""
python3 -m gitvisioncli.cli "$@"

