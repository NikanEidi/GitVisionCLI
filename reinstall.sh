#!/bin/bash
cd /Users/kuroko/Desktop/APPs/GitVisionCLI

# Uninstall
python3 -m pip uninstall -y gitvisioncli 2>/dev/null
rm -f ~/Library/Python/3.14/bin/gitvision

# Clean .bin
rm -rf .bin
mkdir -p .bin

# Install
python3 -m pip install --target .bin --break-system-packages .

# Create launcher
cat > .bin/gitvision << 'LAUNCHER'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$PROJECT_ROOT:$PYTHONPATH"
exec python3 -m gitvisioncli.cli "$@"
LAUNCHER

chmod +x .bin/gitvision

echo "✓ Installation complete in .bin/"
echo "Run: source ~/.zshrc"
