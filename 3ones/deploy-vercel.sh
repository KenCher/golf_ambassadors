#!/bin/bash

# G4K Tournament Manager - Vercel Deployment Script
# This script deploys the tournament manager to Vercel for mobile access

echo "🚀 G4K Tournament Manager - Vercel Deployment"
echo "=============================================="
echo ""

# Check if vercel is installed
if ! command -v vercel &> /dev/null
then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
    echo "✅ Vercel CLI installed!"
    echo ""
fi

# Navigate to project directory
cd "$(dirname "$0")"

echo "📦 Preparing deployment..."
echo ""

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod --yes

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📱 Your tournament manager is now live!"
echo "   Open the URL above on your Android phone"
echo ""
echo "🎯 Quick Access:"
echo "   - Landing Page: /index.html"
echo "   - Course Finder: /g4k-course-finder.html"
echo "   - Tournament Manager: /tournament-manager.html"
echo "   - Deerfield Specific: /deerfield-tournament.html"
echo ""
echo "⛳ Ready to manage tournaments on your phone!"

# Made with Bob
