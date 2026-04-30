# 🚀 Advanced Golf Ambassadors App - Setup Guide

## 📋 What's New

The advanced version includes:
- ✅ **Real-time Score Syncing** - All devices see updates instantly
- ✅ **Player Self-Entry** - Players enter their own scores from any device
- ✅ **Admin Dashboard** - Edit and manage all scores from one place
- ✅ **Live Leaderboard** - See rankings update in real-time
- ✅ **Firebase Backend** - No more localStorage limitations
- ✅ **Multi-Device Support** - Works across all phones, tablets, and computers

## 🎯 New Pages Created

### 1. **Live Score Entry** (`live-score-entry.html`)
   - **URL**: https://golf-ambassadors.web.app/live-score-entry.html
   - **For**: All players
   - **Features**:
     - Select event from dropdown
     - Enter your name
     - Input scores for each hole
     - See live leaderboard
     - Automatic syncing across all devices

### 2. **Admin Dashboard** (`admin-live-dashboard.html`)
   - **URL**: https://golf-ambassadors.web.app/admin-live-dashboard.html
   - **For**: Tournament administrators
   - **Features**:
     - View all player scores in real-time
     - Edit any player's scores
     - Delete incorrect entries
     - See event statistics (total players, average score, etc.)
     - All changes sync instantly to all devices

### 3. **Firebase Config** (`firebase-config.js`)
   - Central configuration file
   - Needs to be updated with your Firebase credentials

## 🔧 Setup Steps

### Step 1: Enable Firebase Realtime Database

1. Go to https://console.firebase.google.com/
2. Select **golf-ambassadors** project
3. Click **Build** → **Realtime Database**
4. Click **Create Database**
5. Choose location: **United States (us-central1)**
6. Select **Start in test mode**
7. Click **Enable**

### Step 2: Get Firebase Configuration

1. In Firebase Console, click ⚙️ gear icon → **Project settings**
2. Scroll to **Your apps** section
3. If no web app exists:
   - Click **Add app** → Web icon `</>`
   - Name it: `Golf Ambassadors Web`
   - Click **Register app**
4. Copy the `firebaseConfig` object

### Step 3: Update firebase-config.js

1. Open `public/firebase-config.js`
2. Replace the placeholder values with your actual config:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_ACTUAL_API_KEY",
  authDomain: "golf-ambassadors.firebaseapp.com",
  databaseURL: "https://golf-ambassadors-default-rtdb.firebaseio.com",
  projectId: "golf-ambassadors",
  storageBucket: "golf-ambassadors.appspot.com",
  messagingSenderId: "YOUR_ACTUAL_SENDER_ID",
  appId: "YOUR_ACTUAL_APP_ID"
};
```

### Step 4: Set Database Security Rules

1. In Firebase Console → **Realtime Database** → **Rules** tab
2. Replace with these rules:

```json
{
  "rules": {
    "events": {
      ".read": true,
      ".write": true,
      "$eventId": {
        ".read": true,
        ".write": true,
        "scores": {
          "$playerId": {
            ".read": true,
            ".write": true
          }
        }
      }
    },
    "courses": {
      ".read": true,
      ".write": true
    }
  }
}
```

3. Click **Publish**

### Step 5: Deploy to Firebase

```bash
./deploy.sh
```

Or manually:
```bash
firebase deploy --only hosting
```

## 📱 How to Use

### For Players:

1. **Open the Score Entry Page**
   - Go to: https://golf-ambassadors.web.app/live-score-entry.html
   - Or scan QR code provided by admin

2. **Select Event**
   - Choose your tournament from the dropdown

3. **Enter Your Name**
   - Type your full name exactly as registered

4. **Enter Scores**
   - Input your score for each hole as you play
   - Scores save automatically
   - See your position on the live leaderboard

5. **Share with Friends**
   - Send the link via WhatsApp
   - Everyone can enter their own scores

### For Admins:

1. **Create Event** (use existing event-registration-admin.html)
   - Create your tournament as usual
   - Event will be saved to Firebase

2. **Share Score Entry Link**
   - Give players: https://golf-ambassadors.web.app/live-score-entry.html
   - Or create QR code for easy access

3. **Monitor Scores**
   - Open: https://golf-ambassadors.web.app/admin-live-dashboard.html
   - Select your event
   - See all scores in real-time

4. **Edit Scores if Needed**
   - Click "Edit" next to any player
   - Modify hole scores
   - Changes sync instantly

5. **View Results**
   - Use existing golf-ambassadors-results.html
   - Or share the live leaderboard view

## 🔄 How Syncing Works

1. **Player enters score** → Saved to Firebase
2. **Firebase broadcasts** → All connected devices receive update
3. **Leaderboards update** → Rankings refresh automatically
4. **Admin edits score** → Changes appear on all devices instantly

## 🎯 Workflow Example

**Tournament Day:**

1. **Admin** creates event "UG Open" at Uganda Golf Club
2. **Admin** shares score entry link via WhatsApp group
3. **Players** open link, select "UG Open", enter their names
4. **Players** enter scores as they play each hole
5. **Everyone** sees live leaderboard updating in real-time
6. **Admin** monitors from dashboard, fixes any errors
7. **After tournament** - all scores are saved and synced

## 🆘 Troubleshooting

### "Offline" Status
- Check internet connection
- Verify Firebase config is correct
- Ensure Realtime Database is enabled

### Events Not Showing
- Make sure you created events using the updated admin page
- Check Firebase Console → Realtime Database → Data tab
- Verify events are stored under `/events/`

### Scores Not Syncing
- Check browser console for errors (F12)
- Verify database rules are published
- Ensure `databaseURL` is in firebase-config.js

## 📊 Data Structure

Firebase stores data like this:

```
/events
  /event-id-123
    name: "UG Open"
    course: "Uganda Golf Club"
    date: "2026-05-01"
    /scores
      /player-john-doe
        playerName: "John Doe"
        total: 85
        /holes
          1: 4
          2: 5
          3: 3
          ...
```

## 🔐 Security Notes

**Current Setup (Test Mode):**
- Anyone can read/write data
- Good for testing and small tournaments
- No authentication required

**For Production:**
- Add Firebase Authentication
- Restrict write access to authenticated users
- Add admin role verification
- See Firebase documentation for security rules

## 📞 Support

If you need help:
1. Check `GET_FIREBASE_CONFIG.md` for config help
2. Check `FIREBASE_DATABASE_SETUP_GUIDE.md` for database setup
3. Review Firebase Console for errors
4. Check browser console (F12) for JavaScript errors

## 🎉 Benefits Over Old Version

| Feature | Old (localStorage) | New (Firebase) |
|---------|-------------------|----------------|
| Multi-device | ❌ No | ✅ Yes |
| Real-time sync | ❌ No | ✅ Yes |
| Player self-entry | ❌ No | ✅ Yes |
| Admin editing | ❌ No | ✅ Yes |
| Data persistence | ⚠️ Per device | ✅ Cloud-based |
| Concurrent users | ❌ No | ✅ Unlimited |
| Live leaderboard | ❌ No | ✅ Yes |

---

**Ready to go live?** Follow the setup steps above and deploy! 🚀⛳