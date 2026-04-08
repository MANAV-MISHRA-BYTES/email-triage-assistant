#!/usr/bin/env bash
# scripts/validate.sh - Local validation script

set -e

echo "🔍 Running Email Triage Assistant Validation..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python
echo "1️⃣  Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check dependencies
echo ""
echo "2️⃣  Checking dependencies..."
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Run tests
echo ""
echo "3️⃣  Running unit tests..."
python -m pytest tests/ -v
echo -e "${GREEN}✅ Tests passed${NC}"

# Validate OpenEnv spec
echo ""
echo "4️⃣  Validating OpenEnv spec..."
if command -v openenv &> /dev/null; then
    openenv validate
    echo -e "${GREEN}✅ OpenEnv validation passed${NC}"
else
    echo -e "${YELLOW}⚠️  openenv CLI not found, skipping${NC}"
fi

# Start server in background
echo ""
echo "5️⃣  Testing server startup..."
uvicorn server.main:app --host 127.0.0.1 --port 8765 &
SERVER_PID=$!
sleep 3

# Test endpoints
echo ""
echo "6️⃣  Testing API endpoints..."

# Health check
if curl -s http://127.0.0.1:8765/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health endpoint working${NC}"
else
    echo -e "${RED}❌ Health endpoint failed${NC}"
    kill $SERVER_PID
    exit 1
fi

# Reset endpoint
if curl -s -X POST http://127.0.0.1:8765/reset \
    -H "Content-Type: application/json" \
    -d '{"task_name": "easy_categorization"}' | grep -q "inbox"; then
    echo -e "${GREEN}✅ Reset endpoint working${NC}"
else
    echo -e "${RED}❌ Reset endpoint failed${NC}"
    kill $SERVER_PID
    exit 1
fi

# State endpoint
if curl -s http://127.0.0.1:8765/state | grep -q "inbox"; then
    echo -e "${GREEN}✅ State endpoint working${NC}"
else
    echo -e "${RED}❌ State endpoint failed${NC}"
    kill $SERVER_PID
    exit 1
fi

# Stop server
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true

# Docker build
echo ""
echo "7️⃣  Testing Docker build..."
if command -v docker &> /dev/null; then
    docker build -t email-triage-test . > /dev/null 2>&1
    echo -e "${GREEN}✅ Docker build successful${NC}"
    docker rmi email-triage-test > /dev/null 2>&1
else
    echo -e "${YELLOW}⚠️  Docker not found, skipping${NC}"
fi

echo ""
echo -e "${GREEN}🎉 All validations passed!${NC}"
echo ""
echo "Ready to deploy to Hugging Face Spaces!"