#!/usr/bin/env bash
# ============================================================
#  VA Creator Launcher — macOS (.command)
#  Double-click this file in Finder to launch VA Creator
#  Starts the Streamlit dashboard for VA Creator
# ============================================================

set -e

echo ""
echo " ========================================"
echo "  VA Creator v1.3.0 — Launcher (macOS)"
echo " ========================================"
echo ""

# Navigate to the script's own directory (critical for .command files
# launched by double-clicking in Finder)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# --- Check Python ---
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python is not installed or not in PATH."
    echo "        Please install Python 3.10+ from https://www.python.org/"
    echo ""
    echo "Press any key to close..."
    read -n 1
    exit 1
fi

echo "[INFO] Using Python: $($PYTHON_CMD --version)"

# --- Check / Create Virtual Environment ---
if [ ! -f "venv/bin/activate" ]; then
    echo "[INFO] Virtual environment not found. Creating one..."
    $PYTHON_CMD -m venv venv
    echo "[OK] Virtual environment created."
fi

# --- Activate Virtual Environment ---
source venv/bin/activate

# --- Install Python Dependencies ---
if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing Python dependencies..."
    pip install -r requirements.txt --quiet
    echo "[OK] Python dependencies installed."
fi

# --- Install Node.js Dependencies (if package.json exists) ---
if [ -f "package.json" ]; then
    if command -v npm &>/dev/null; then
        if [ ! -d "node_modules" ]; then
            echo "[INFO] Installing Node.js dependencies..."
            npm install --quiet
            echo "[OK] Node.js dependencies installed."
        fi
    else
        echo "[WARNING] npm not found. MCP server integrations may not work."
        echo "         Install Node.js from https://nodejs.org/ for full functionality."
    fi
fi

# --- Check .env File ---
if [ ! -f ".env" ]; then
    echo ""
    echo "[WARNING] .env file not found!"
    echo "         Copy env.example to .env and add your API keys:"
    echo "           cp env.example .env"
    echo ""
fi

# --- Launch Streamlit ---
echo ""
echo "[INFO] Starting VA Creator Dashboard..."
echo "       Open http://localhost:8501 in your browser."
echo "       Press Ctrl+C to stop the server."
echo ""

streamlit run app.py
