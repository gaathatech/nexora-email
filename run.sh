#!/bin/bash
# Nexora Email Engine - Quick Start

echo "🚀 Starting Nexora Email Engine..."
echo ""

# Kill any existing processes
pkill -f "python.*app.py" 2>/dev/null || true

# Start the app
cd "$(dirname "$0")"
python3 app.py

# If we reach here, the app was stopped
echo ""
echo "❌ App stopped"
