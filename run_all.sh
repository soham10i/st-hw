#!/bin/bash
# STF Digital Twin - Run All Services

echo "=============================================="
echo "STF Digital Twin - Starting All Services"
echo "=============================================="

# Set environment variables
export DATABASE_URL="${DATABASE_URL:-mysql+pymysql://stf_user:stf_password@localhost:3306/stf_warehouse}"
export STF_API_URL="${STF_API_URL:-http://localhost:8000}"
export MQTT_BROKER="${MQTT_BROKER:-localhost}"
export MQTT_PORT="${MQTT_PORT:-1883}"

# Check if Docker services are running
echo "Checking Docker services..."
if ! docker ps | grep -q stf_mysql; then
    echo "Starting Docker infrastructure..."
    docker-compose up -d
    sleep 5
fi

# Start services in background
echo "Starting FastAPI server..."
python -m api.main &
API_PID=$!
sleep 2

echo "Starting Mock Hardware..."
python -m hardware.mock_hbw &
HW_PID=$!
sleep 1

echo "Starting Main Controller..."
python -m controller.main_controller &
CTRL_PID=$!
sleep 1

echo "Starting Streamlit Dashboard..."
streamlit run dashboard/app.py --server.port 8501 &
DASH_PID=$!

echo ""
echo "=============================================="
echo "All services started!"
echo "=============================================="
echo "FastAPI API:    http://localhost:8000/docs"
echo "Dashboard:      http://localhost:8501"
echo "Adminer (DB):   http://localhost:8080"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $API_PID $HW_PID $CTRL_PID $DASH_PID 2>/dev/null; exit" INT TERM
wait
