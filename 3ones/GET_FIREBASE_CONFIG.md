# 🔑 How to Get Your Firebase Configuration

## Quick Steps

1. **Open Firebase Console**
   - Go to: https://console.firebase.google.com/
   - Select project: **golf-ambassadors**

2. **Go to Project Settings**
   - Click the ⚙️ gear icon next to "Project Overview" (top left)
   - Click "Project settings"

3. **Scroll Down to "Your apps"**
   - Look for the "Your apps" section
   - If you see a web app already, click on it
   - If not, click "Add app" → Select Web icon `</>`

4. **Register App (if creating new)**
   - App nickname: `Golf Ambassadors Web`
   - Check "Also set up Firebase Hosting"
   - Click "Register app"

5. **Copy the Config**
   - You'll see code like this:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "golf-ambassadors.firebaseapp.com",
  databaseURL: "https://golf-ambassadors-default-rtdb.firebaseio.com",
  projectId: "golf-ambassadors",
  storageBucket: "golf-ambassadors.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef123456"
};
```

6. **Update firebase-config.js**
   - Open: `public/firebase-config.js`
   - Replace the placeholder values with your actual config
   - Save the file

## Important Notes

- ⚠️ The `databaseURL` is REQUIRED for Realtime Database
- ⚠️ If you don't see `databaseURL`, you need to enable Realtime Database first
- ⚠️ Keep your `apiKey` safe (though it's okay to expose in client-side code)

## Enable Realtime Database

If you haven't enabled Realtime Database yet:

1. In Firebase Console, click "Build" → "Realtime Database"
2. Click "Create Database"
3. Choose location: **United States (us-central1)**
4. Start in **test mode** (for now)
5. Click "Enable"

After enabling, go back to Project Settings to get the updated config with `databaseURL`.

## Test Your Config

After updating `firebase-config.js`:

1. Open: https://golf-ambassadors.web.app/live-score-entry.html
2. Check the status badge at the top
3. If it says "✓ Connected", your config is working!
4. If it says "✗ Offline", double-check your config values

## Need Help?

If you're stuck, you can:
1. Send me a screenshot of your Firebase Console
2. Copy-paste the config code (it's safe to share)
3. Or I can create a script to help you retrieve it automatically