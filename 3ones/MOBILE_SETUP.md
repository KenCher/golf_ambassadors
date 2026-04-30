# Golf4us - Mobile Testing Guide 📱

## How to Test on Your Android Phone

There are several ways to test the Golf4us app on your Android phone:

---

## Method 1: Using Python HTTP Server (Recommended - Easiest)

### Step 1: Start a Local Web Server on Your Mac

```bash
# Navigate to the Golf4us directory
cd ~/Golf4us/public

# Start Python HTTP server (Python 3)
python3 -m http.server 8000

# Or if you have Python 2
python -m SimpleHTTPServer 8000
```

You should see: `Serving HTTP on 0.0.0.0 port 8000 ...`

### Step 2: Find Your Mac's IP Address

```bash
# On Mac, run:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Look for something like: inet 192.168.1.XXX
```

### Step 3: Access from Your Android Phone

1. Make sure your phone is on the **same WiFi network** as your Mac
2. Open Chrome or any browser on your Android phone
3. Go to: `http://YOUR_MAC_IP:8000/mobile.html`
   - Example: `http://192.168.1.100:8000/mobile.html`

---

## Method 2: Using Node.js HTTP Server

### Step 1: Install http-server (one-time setup)

```bash
npm install -g http-server
```

### Step 2: Start the Server

```bash
cd ~/Golf4us/public
http-server -p 8000
```

### Step 3: Access from Android

Same as Method 1, Step 3 above.

---

## Method 3: File Transfer to Phone

### Option A: Email the File

1. Email `mobile.html` to yourself
2. Open the email on your Android phone
3. Download and open the file in Chrome

### Option B: Google Drive

1. Upload `mobile.html` to Google Drive
2. Open it on your phone from the Drive app
3. Open with Chrome browser

### Option C: USB Transfer

1. Connect your phone to Mac via USB
2. Enable File Transfer mode on Android
3. Copy `mobile.html` to your phone's Downloads folder
4. Open with Chrome browser

---

## Method 4: Using ngrok (For Remote Access)

If you want to access it from anywhere (not just local network):

### Step 1: Install ngrok

```bash
# Download from https://ngrok.com/download
# Or use Homebrew:
brew install ngrok
```

### Step 2: Start Local Server

```bash
cd ~/Golf4us/public
python3 -m http.server 8000
```

### Step 3: Create Tunnel

```bash
# In a new terminal:
ngrok http 8000
```

### Step 4: Access from Phone

Use the HTTPS URL provided by ngrok (e.g., `https://abc123.ngrok.io/mobile.html`)

---

## Testing the Mobile Interface

### Features to Test:

1. **Leaderboard Tab** 📊
   - Toggle between Gross and Net scores
   - View player rankings
   - Check score-to-par calculations

2. **Score Entry Tab** ✏️
   - Select a player
   - Select a hole (1-18)
   - Enter strokes
   - Submit score
   - Verify success message

3. **Skins Game Tab** 💰
   - Toggle between Gross and Net skins
   - View hole-by-hole results
   - Check carryovers

4. **Players Tab** 👥
   - View all players
   - Check handicaps
   - See holes completed

5. **Refresh Button** ↻
   - Tap the circular button in bottom-right
   - Verify data updates

### Mobile-Specific Features:

- ✅ Touch-friendly buttons (large tap targets)
- ✅ Swipeable tabs
- ✅ Responsive design (works on all screen sizes)
- ✅ No zoom required
- ✅ Optimized for portrait mode
- ✅ Fast loading
- ✅ Works offline after first load

---

## Troubleshooting

### Can't Connect from Phone?

1. **Check WiFi**: Ensure both devices are on the same network
2. **Check Firewall**: Mac firewall might be blocking connections
   - Go to System Preferences → Security & Privacy → Firewall
   - Click "Firewall Options"
   - Ensure Python/Node is allowed
3. **Check IP Address**: Make sure you're using the correct IP
4. **Try Different Port**: Use 8080 or 3000 if 8000 doesn't work

### Page Not Loading?

1. Clear browser cache on Android
2. Try a different browser (Chrome, Firefox, Samsung Internet)
3. Check if server is still running on Mac
4. Restart the server

### Features Not Working?

1. Make sure JavaScript is enabled in your browser
2. Try refreshing the page
3. Check browser console for errors (Chrome DevTools)

---

## Quick Start Commands

```bash
# Easiest way to start:
cd ~/Golf4us/public
python3 -m http.server 8000

# Find your IP:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Then on your phone, go to:
# http://YOUR_IP:8000/mobile.html
```

---

## Advanced: Install as PWA (Progressive Web App)

The mobile interface can be installed as an app on your phone:

1. Open `mobile.html` in Chrome on Android
2. Tap the menu (⋮) in top-right
3. Select "Add to Home screen"
4. The app will appear on your home screen like a native app!

---

## Sample Data Included

The mobile interface comes pre-loaded with 4 sample players:
- Tiger Woods (Handicap: 2.5)
- Phil Mickelson (Handicap: 5.8)
- Rory McIlroy (Handicap: 1.2)
- Jordan Spieth (Handicap: 3.4)

You can start entering scores immediately to test all features!

---

## Need Help?

If you encounter any issues:
1. Check that your Mac and phone are on the same WiFi
2. Verify the server is running (you should see logs in terminal)
3. Try accessing from Mac first: `http://localhost:8000/mobile.html`
4. Check Mac firewall settings

---

**Enjoy testing Golf4us on your Android phone! ⛳📱**