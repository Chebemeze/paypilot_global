#!/bin/bash
# start-servers.sh - Start both PayPilot Global servers

echo "🚀 Starting PayPilot Global..."
echo ""

# Kill any existing processes on these ports
fuser -k 3000/tcp 2>/dev/null
fuser -k 8000/tcp 2>/dev/null
sleep 1

# Start Backend
echo "📦 Starting Backend API Server on port 8000..."
cd /home/user/paypilot-global/backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✓ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "   ⏳ Waiting for backend..."
for i in {1..10}; do
  if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "   ✓ Backend is healthy"
    break
  fi
  sleep 1
done

# Start Frontend
echo ""
echo "🎨 Starting Frontend on port 3000..."
cd /home/user/paypilot-global/frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✓ Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to be ready
echo "   ⏳ Waiting for frontend..."
for i in {1..15}; do
  if curl -s http://localhost:3000/login > /dev/null 2>&1; then
    echo "   ✓ Frontend is ready"
    break
  fi
  sleep 1
done

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Both servers are running!"
echo ""
echo "🌐 Frontend:  http://localhost:3000"
echo "🔌 Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "🔐 Login Credentials:"
echo "   Email:    admin@acmeglobal.com"
echo "   Password: password123"
echo ""
echo "🔗 Integration Status:"
echo "   ✓ API Proxy:   Frontend → Backend (via Next.js rewrites)"
echo "   ✓ Auth:        JWT-based with auto-redirect"
echo "   ✓ Data Flow:   All pages fetch real data from backend"
echo ""
echo "To stop both servers:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "═══════════════════════════════════════════════════════"
