#!/bin/bash
# Setup rust-twins-mut on a bare Ubuntu machine.
#
# Usage:
#   ./setup.sh                  # interactive (opens browser for gcloud auth)
#   ./setup.sh --no-browser     # headless (prints URL to auth from another machine)
#
# Prerequisites: a GCP project with GPT-OSS API enabled in Model Garden.

set -euo pipefail

NO_BROWSER=false
for arg in "$@"; do
    case "$arg" in
        --no-browser) NO_BROWSER=true ;;
    esac
done

echo "=========================================="
echo "  rust-twins-mut setup"
echo "=========================================="
echo

# --- 1. System packages ---
echo "[1/5] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq git curl python3 python3-venv > /dev/null

# --- 2. Google Cloud CLI ---
if command -v gcloud &> /dev/null; then
    echo "[2/5] gcloud CLI already installed: $(gcloud --version 2>&1 | head -1)"
else
    echo "[2/5] Installing Google Cloud CLI..."
    # https://cloud.google.com/sdk/docs/install#deb
    sudo apt-get install -y -qq apt-transport-https ca-certificates gnupg > /dev/null
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
        | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg 2>/dev/null
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
        | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq google-cloud-cli > /dev/null
    echo "  gcloud installed: $(gcloud --version 2>&1 | head -1)"
fi

# --- 3. gcloud auth ---
echo "[3/5] Google Cloud authentication..."
echo "  This step requires you to log in with a Google account."
echo

if [ "$NO_BROWSER" = true ]; then
    echo "  --no-browser mode: you'll get a URL to open on another machine."
    echo
    gcloud init --no-launch-browser
    gcloud auth application-default login --no-launch-browser
else
    echo "  A browser window will open for login."
    echo "  (Use --no-browser flag if running on a headless server.)"
    echo
    gcloud init
    gcloud auth application-default login
fi

# --- 4. uv ---
if command -v uv &> /dev/null; then
    echo "[4/5] uv already installed: $(uv --version)"
else
    echo "[4/5] Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add to current session PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo "  uv installed: $(uv --version)"
fi

# --- 5. Project setup ---
echo "[5/5] Setting up project..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

git submodule update --init --recursive
uv sync

echo
echo "=========================================="
echo "  Setup complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "  1. Set your GCP project ID:"
echo "     Edit gpt-oss-20b-google-cloud-call/config.py"
echo
echo "  2. Enable GPT-OSS API in Model Garden:"
echo "     https://console.cloud.google.com/vertex-ai/model-garden"
echo
echo "  3. Run:"
echo "     uv run python -m rust_twins_mut ./seeds"
