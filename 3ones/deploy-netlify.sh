#!/bin/bash

# Golf4us Netlify Deployment Script
# Deploys the GPS-enabled Golf4us app to Netlify

echo "🏌️  Golf4us - Netlify Deployment"
echo "=================================="
echo ""

# Check if netlify CLI is installed
if ! command -v netlify &> /dev/null; then
    echo "📦 Netlify CLI not found. Installing..."
    npm install -g netlify-cli
    echo ""
fi

echo "🚀 Deploying to Netlify..."
echo ""

# Deploy to production
netlify deploy --prod

echo ""
echo "=================================="
echo "✅ Deployment complete!"
echo ""
echo "📱 Access GPS interface on your phone:"
echo "   https://YOUR-SITE.netlify.app/gps-mobile.html"
echo ""
echo "📋 Other pages:"
echo "   Main app: https://YOUR-SITE.netlify.app/"
echo "   Mobile: https://YOUR-SITE.netlify.app/mobile.html"
echo ""
echo "💡 Tip: Bookmark the GPS page on your phone for quick access!"
echo "=================================="

# Made with Bob
