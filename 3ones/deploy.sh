#!/bin/bash

# Simple Golf Ambassadors Deployment Script
# This script deploys the app to Firebase Hosting

echo "🏌️ Golf Ambassadors - Simple Deployment"
echo "========================================"
echo ""

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI is not installed."
    echo "Install it with: npm install -g firebase-tools"
    exit 1
fi

echo "✅ Firebase CLI found"
echo ""

# Check if logged in to Firebase
if ! firebase projects:list &> /dev/null; then
    echo "❌ Not logged in to Firebase."
    echo "Run: firebase login"
    exit 1
fi

echo "✅ Firebase authentication verified"
echo ""

# Deploy to Firebase Hosting
echo "🚀 Deploying to Firebase Hosting..."
echo ""

firebase deploy --only hosting

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Your app is live at: https://golf-ambassadors.web.app"
    echo ""
else
    echo ""
    echo "❌ Deployment failed. Please check the error messages above."
    exit 1
fi

# Made with Bob
