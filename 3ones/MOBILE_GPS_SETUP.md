# Mobile GPS Setup Guide - Android Testing

Quick guide to test the GPS features on your Android phone.

## Option 1: Local Network Testing (Recommended)

This method allows you to test on your phone while connected to the same WiFi network as your computer.

### Step 1: Start Local Server

In your Golf4us directory, run:

```bash
# Using Python (if installed)
python3 -m http.server 8080

# OR using Node.js (if you have it)
npx http-server -p 8080

# OR using PHP (if installed)
php -S localhost:8080
```

### Step 2: Find Your Computer's IP Address

**On Mac:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**On Windows:**
```bash
ipconfig
```

Look for your local IP address (usually starts with 192.168.x.x or 10.0.x.x)

### Step 3: Access on Android Phone

1. Make sure your phone is on the **same WiFi network** as your computer
2. Open Chrome or Firefox on your Android phone
3. Navigate to: `http://YOUR_IP_ADDRESS:8080/public/gps-mobile.html`
   - Example: `http://192.168.1.100:8080/public/gps-mobile.html`
4. Allow location permissions when prompted
5. Start testing!

**Note:** GPS requires HTTPS for security. For local testing, most browsers allow HTTP on local networks.

---

## Option 2: Deploy to Free Hosting (Best for Real Testing)

For full GPS functionality with HTTPS, deploy to a free hosting service.

### A. Deploy to Netlify (Easiest)

1. **Install Netlify CLI:**
   ```bash
   npm install -g netlify-cli
   ```

2. **Deploy:**
   ```bash
   cd /Users/kencheru/Golf4us
   netlify deploy --prod
   ```

3. **Follow prompts:**
   - Authorize Netlify
   - Create new site or link existing
   - Publish directory: `.` (current directory)

4. **Access on phone:**
   - You'll get a URL like: `https://your-site.netlify.app`
   - Open on your Android phone: `https://your-site.netlify.app/public/gps-mobile.html`

### B. Deploy to Vercel

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   cd /Users/kencheru/Golf4us
   vercel --prod
   ```

3. **Access on phone:**
   - You'll get a URL like: `https://your-site.vercel.app`
   - Open: `https://your-site.vercel.app/public/gps-mobile.html`

### C. Deploy to GitHub Pages

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add GPS features"
   git push origin main
   ```

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: Deploy from branch `main`
   - Folder: `/ (root)`
   - Save

3. **Access on phone:**
   - URL: `https://YOUR_USERNAME.github.io/Golf4us/public/gps-mobile.html`

---

## Option 3: Quick Test with ngrok (Temporary URL)

Perfect for quick testing without deployment.

1. **Install ngrok:**
   - Download from: https://ngrok.com/download
   - Or: `brew install ngrok` (Mac)

2. **Start local server:**
   ```bash
   cd /Users/kencheru/Golf4us
   python3 -m http.server 8080
   ```

3. **In another terminal, start ngrok:**
   ```bash
   ngrok http 8080
   ```

4. **Access on phone:**
   - ngrok will show a URL like: `https://abc123.ngrok.io`
   - Open on Android: `https://abc123.ngrok.io/public/gps-mobile.html`
   - This URL works from anywhere!

---

## Testing Checklist

Once you have the GPS interface open on your phone:

### Initial Setup
- [ ] Allow location permissions when prompted
- [ ] Wait for GPS to acquire signal (green indicator)
- [ ] Verify distance display shows "---" then updates with a number

### Basic Features
- [ ] Distance to green updates as you move
- [ ] Compass arrow rotates to point toward target
- [ ] Direction shows (N, NE, E, SE, S, SW, W, NW)
- [ ] GPS accuracy shows in meters

### Shot Tracking
- [ ] Tap "Mark Shot" button
- [ ] Shot appears in shot history
- [ ] Distance between shots calculated
- [ ] Shot counter increments

### Navigation
- [ ] Tap "Next Hole" to advance
- [ ] Hole number updates
- [ ] Par and yardage change
- [ ] Shot history clears for new hole

### Performance
- [ ] Interface is responsive
- [ ] Updates happen smoothly
- [ ] No lag or freezing
- [ ] Battery usage is reasonable

---

## Troubleshooting

### "Location permission denied"
- Go to Android Settings → Apps → Chrome/Firefox → Permissions
- Enable Location permission
- Reload the page

### "GPS unavailable"
- Ensure Location Services are enabled in Android Settings
- Try moving to an area with clear sky view
- Restart the browser

### Distance not updating
- Check GPS accuracy indicator (should be green or yellow)
- Move around a bit to trigger updates
- Verify you're outdoors with good GPS signal

### Page won't load
- Verify your phone is on the same WiFi network (Option 1)
- Check the IP address is correct
- Try accessing from computer browser first to verify server is running
- For deployed versions, check the URL is correct

### HTTPS required error
- Use Option 2 (deployment) or Option 3 (ngrok) for full GPS functionality
- Local HTTP may work on some browsers but HTTPS is recommended

---

## Recommended Testing Approach

1. **Start with Option 1** (local network) to verify basic functionality
2. **Use Option 3** (ngrok) for quick outdoor testing with HTTPS
3. **Deploy with Option 2** (Netlify/Vercel) for permanent access

---

## Next Steps After Testing

Once you've verified GPS works on your phone:

1. **Collect real course data:**
   - Walk your local course
   - Mark tee boxes and greens
   - Note hazard locations
   - Record coordinates

2. **Update course data:**
   - Add GPS coordinates to course setup
   - Test with real hole data
   - Verify distances are accurate

3. **Use during a round:**
   - Keep phone charged (GPS uses battery)
   - Use for club selection
   - Track your shots
   - Review data after round

---

## Support

If you encounter issues:
- Check GPS_GUIDE.md for detailed troubleshooting
- Verify GPS is enabled on your device
- Ensure you're outdoors with clear sky view
- Try different browsers (Chrome recommended)

Happy golfing! ⛳