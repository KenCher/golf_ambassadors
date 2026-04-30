# 🏌️ Golf Ambassadors - Simple Deployment Guide

This guide explains how to easily deploy your Golf Ambassadors app.

## Quick Deploy (One Command)

```bash
./deploy.sh
```

That's it! The script will:
- ✅ Check if Firebase CLI is installed
- ✅ Verify you're logged in
- ✅ Deploy your app to Firebase Hosting
- ✅ Show you the live URL

## First Time Setup

If this is your first time deploying, follow these steps:

### 1. Install Firebase CLI (One Time Only)

```bash
npm install -g firebase-tools
```

### 2. Login to Firebase (One Time Only)

```bash
firebase login
```

This will open your browser to authenticate with Google.

### 3. Deploy!

```bash
./deploy.sh
```

## Manual Deployment (Alternative)

If you prefer to deploy manually without the script:

```bash
firebase deploy --only hosting
```

## What Gets Deployed?

The deployment includes all files in the `public/` folder:
- `golf-ambassadors.html` - Score entry page
- `golf-ambassadors-results.html` - Results/leaderboard page
- `event-registration-admin.html` - Event management
- `event-registration.html` - Player registration
- All other HTML, JSON, and asset files

## Live URL

After deployment, your app is available at:
**https://golf-ambassadors.web.app**

## Troubleshooting

### "Firebase CLI not found"
Install it: `npm install -g firebase-tools`

### "Not logged in to Firebase"
Login: `firebase login`

### "Permission denied: ./deploy.sh"
Make it executable: `chmod +x deploy.sh`

### Deployment fails
1. Check your internet connection
2. Verify you're in the correct directory (`/Users/kencheru/3ones`)
3. Make sure `firebase.json` exists in the project root
4. Try manual deployment: `firebase deploy --only hosting`

## Project Structure

```
3ones/
├── deploy.sh                          # Simple deployment script
├── firebase.json                      # Firebase configuration
├── public/                            # All web files (gets deployed)
│   ├── golf-ambassadors.html         # Main score entry
│   ├── golf-ambassadors-results.html # Leaderboard
│   ├── event-registration-admin.html # Event management
│   └── ...other files
└── SIMPLE_DEPLOYMENT_GUIDE.md        # This file
```

## Key Features

✅ **Mobile Optimized** - Works on iPhone and Android  
✅ **PWA Ready** - Can be installed as an app  
✅ **Firebase Hosting** - Fast, secure, and reliable  
✅ **One-Command Deploy** - Simple `./deploy.sh`  
✅ **No Build Step** - Pure HTML/CSS/JS, no compilation needed

## Making Changes

1. Edit files in the `public/` folder
2. Test locally by opening HTML files in your browser
3. Deploy with `./deploy.sh`
4. Changes are live immediately!

## Support

- Firebase Console: https://console.firebase.google.com/project/golf-ambassadors
- Firebase Documentation: https://firebase.google.com/docs/hosting

---

**Remember**: The app is already deployed and working at https://golf-ambassadors.web.app