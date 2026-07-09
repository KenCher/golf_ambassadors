#!/bin/bash

# Golf4us GPS Mobile Server Starter
# Quick script to start a local server for testing GPS on mobile devices

echo "🏌️  Golf4us GPS Mobile Server"
echo "================================"
echo ""

# Get local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
else
    # Windows (Git Bash)
    LOCAL_IP=$(ipconfig | grep "IPv4" | awk '{print $NF}' | head -n 1)
fi

echo "📍 Your local IP address: $LOCAL_IP"
echo ""

# Check for available server options
if command -v python3 &> /dev/null; then
    echo "✅ Starting Python HTTP server on port 8080..."
    echo ""
    echo "📱 Open on your Android phone:"
    echo "   http://$LOCAL_IP:8080/public/gps-mobile.html"
    echo ""
    echo "⚠️  Make sure your phone is on the same WiFi network!"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "================================"
    echo ""
    python3 -m http.server 8080
elif command -v python &> /dev/null; then
    echo "✅ Starting Python HTTP server on port 8080..."
    echo ""
    echo "📱 Open on your Android phone:"
    echo "   http://$LOCAL_IP:8080/public/gps-mobile.html"
    echo ""
    echo "⚠️  Make sure your phone is on the same WiFi network!"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "================================"
    echo ""
    python -m SimpleHTTPServer 8080
elif command -v php &> /dev/null; then
    echo "✅ Starting PHP server on port 8080..."
    echo ""
    echo "📱 Open on your Android phone:"
    echo "   http://$LOCAL_IP:8080/public/gps-mobile.html"
    echo ""
    echo "⚠️  Make sure your phone is on the same WiFi network!"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "================================"
    echo ""
    php -S 0.0.0.0:8080
elif command -v npx &> /dev/null; then
    echo "✅ Starting Node.js HTTP server on port 8080..."
    echo ""
    echo "📱 Open on your Android phone:"
    echo "   http://$LOCAL_IP:8080/public/gps-mobile.html"
    echo ""
    echo "⚠️  Make sure your phone is on the same WiFi network!"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "================================"
    echo ""
    npx http-server -p 8080
else
    echo "❌ No suitable HTTP server found!"
    echo ""
    echo "Please install one of the following:"
    echo "  - Python 3: brew install python3"
    echo "  - Node.js: brew install node"
    echo "  - PHP: brew install php"
    echo ""
    echo "Or see MOBILE_GPS_SETUP.md for alternative methods"
fi

# Made with Bob
