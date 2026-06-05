#!/bin/bash
# Test connection to laptop server

# Load server URL from config
SERVER_URL=$(python3 -c "import json; print(json.load(open('config.json'))['server_url'])")

echo "🔍 Testing connection to server..."
echo "Server: $SERVER_URL"
echo ""

# Test ping
LAPTOP_IP=$(echo $SERVER_URL | sed 's|http://||' | sed 's|:.*||')
echo "1️⃣ Testing network connectivity..."
if ping -c 2 $LAPTOP_IP > /dev/null 2>&1; then
    echo "   ✅ Laptop is reachable at $LAPTOP_IP"
else
    echo "   ❌ Cannot ping laptop at $LAPTOP_IP"
    echo "   Make sure both devices are on the same WiFi network!"
    exit 1
fi

echo ""
echo "2️⃣ Testing server HTTP endpoint..."
if curl -s --connect-timeout 3 $SERVER_URL/ > /dev/null; then
    echo "   ✅ Server is running!"
    echo ""
    echo "Server info:"
    curl -s $SERVER_URL/ | python3 -m json.tool
else
    echo "   ❌ Server is not responding"
    echo "   Make sure Flask server is running on your laptop:"
    echo "   cd ~/grad_proj/web_app/mesba7/backend"
    echo "   python3 app.py"
    exit 1
fi

echo ""
echo "3️⃣ Testing telemetry upload endpoint..."
TEST_DATA='{"car_id":"TEST","speed":0,"battery":100,"temperature":25,"gps":{"lat":30.0,"lon":31.0},"crash":false,"mode":"manual"}'

RESPONSE=$(curl -s -X POST $SERVER_URL/api/telemetry \
    -H "Content-Type: application/json" \
    -d "$TEST_DATA")

if echo $RESPONSE | grep -q "success"; then
    echo "   ✅ Telemetry endpoint working!"
else
    echo "   ⚠️  Unexpected response:"
    echo "   $RESPONSE"
fi

echo ""
echo "✅ All tests passed! Ready to start car client."
echo ""
echo "Next: Edit config.json and set the correct server_url"
echo "Then: ./start_car.sh"
