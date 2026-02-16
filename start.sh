#!/bin/bash
set -e

echo "🚀 Starting TestStrategy Agent..."

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "❌ Python 3.10+ required"; exit 1; }

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd teststrategy-agent/backend
pip install -r requirements.txt --quiet

# Install frontend dependencies & build
echo "📦 Building frontend..."
cd ../frontend
npm install --silent
npm run build

# Copy build to backend static folder
rm -rf ../backend/static
cp -r dist ../backend/static

# Start the server
cd ../backend
echo ""
echo "✅ TestStrategy Agent is ready!"
echo "🌐 Open http://localhost:8000 in your browser"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000
