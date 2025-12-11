#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Planck AI...${NC}"

# Start Backend
echo -e "${GREEN}📦 Setting up Backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Start backend in background
echo -e "${GREEN}✅ Starting FastAPI Backend on http://localhost:8000${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend
cd ../frontend
echo -e "${GREEN}📦 Setting up Frontend...${NC}"

# Install npm dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start frontend
echo -e "${GREEN}✅ Starting React Frontend on http://localhost:5173${NC}"
npm run dev &
FRONTEND_PID=$!

echo -e "${BLUE}🎉 AgentX is running!${NC}"
echo -e "Frontend: http://localhost:5173"
echo -e "Backend:  http://localhost:8000"
echo -e "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
