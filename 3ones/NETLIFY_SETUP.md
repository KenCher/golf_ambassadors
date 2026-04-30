# Netlify Setup Guide for Golf4us GPS

Step-by-step guide to deploy Golf4us with GPS features to Netlify.

## Quick Deploy (Recommended)

### Option 1: One-Command Deploy

```bash
cd /Users/kencheru/Golf4us
./deploy-netlify.sh
```

This script will:
1. Install Netlify CLI if needed
2. Deploy your app to production
3. Give you the URL to access on your phone

---

## Manual Setup (If you prefer step-by-step)

### Step 1: Install Netlify CLI

```bash
npm install -g netlify-cli
```

### Step 2: Login to Netlify

```bash
netlify login
```

This will:
- Open your browser
- Ask you to authorize the CLI
- Connect your terminal to your Netlify account

### Step 3: Initialize Your Site (First Time Only)

```bash
cd /Users/kencheru/Golf4us
netlify init
```

Follow the prompts:
- **Create & configure a new site**: Yes
- **Team**: Choose your team (or personal)
- **Site name**: golf4us-gps (or your preferred name)
- **Build command**: Leave empty (press Enter)
- **Directory to deploy**: `public`
- **Netlify functions folder**: Leave empty (press Enter)

### Step 4: Deploy to Production

```bash
netlify deploy --prod
```

The CLI will:
- Upload your files
- Deploy to production
- Give you a URL like: `https://golf4us-gps.netlify.app`

---

## Access Your GPS App

Once deployed, you can access:

### GPS Mobile Interface (Main one for your phone)
```
https://YOUR-SITE.netlify.app/gps-mobile.html
```

### Other Pages
```
Main app: https://YOUR-SITE.netlify.app/
Mobile scoring: https://YOUR-SITE.netlify.app/mobile.html
Desktop: https://YOUR-SITE.netlify.app/index.html
```

---

## Using on Your Android Phone

### Step 1: Open the GPS Interface
1. Open Chrome on your Android phone
2. Navigate to: `https://YOUR-SITE.netlify.app/gps-mobile.html`
3. Bookmark it for easy access

### Step 2: Add to Home Screen (Optional but Recommended)
1. Tap the menu (⋮) in Chrome
2. Select "Add to Home screen"
3. Name it "Golf GPS"
4. Tap "Add"

Now you have a GPS app icon on your home screen! 📱⛳

### Step 3: Allow Location Permissions
1. When you first open the app, it will ask for location access
2. Tap "Allow" or "While using the app"
3. Wait for GPS to lock (green indicator)

### Step 4: Start Using!
- Distance to green updates automatically
- Tap "Mark Shot" after each shot
- Tap "Next Hole" to advance
- View shot history and distances

---

## Updating Your Deployment

Whenever you make changes to the code:

```bash
cd /Users/kencheru/Golf4us
./deploy-netlify.sh
```

Or manually:
```bash
netlify deploy --prod
```

Your phone will automatically get the updates next time you refresh!

---

## Netlify Dashboard

Access your deployment dashboard at:
```
https://app.netlify.com
```

From there you can:
- View deployment history
- See site analytics
- Configure custom domain
- Set up environment variables
- View build logs

---

## Custom Domain (Optional)

If you want a custom domain like `golf.yourdomain.com`:

1. Go to Netlify Dashboard
2. Select your site
3. Go to "Domain settings"
4. Click "Add custom domain"
5. Follow the DNS configuration instructions

---

## Troubleshooting

### "Command not found: netlify"
```bash
npm install -g netlify-cli
```

### "Not authorized"
```bash
netlify logout
netlify login
```

### "Deploy failed"
- Check that you're in the correct directory
- Verify `netlify.toml` exists
- Try: `netlify deploy --prod --debug` for more info

### GPS not working on deployed site
- Netlify automatically provides HTTPS ✅
- Make sure location permissions are enabled on your phone
- Try in an outdoor area with clear sky view

### Site is slow to load
- Netlify has global CDN, should be fast
- Check your internet connection
- Try clearing browser cache

---

## Environment Variables (If Needed Later)

To add environment variables:

```bash
netlify env:set VARIABLE_NAME "value"
```

Or in the Netlify Dashboard:
1. Site settings → Environment variables
2. Add variable
3. Redeploy

---

## Monitoring

### View Logs
```bash
netlify logs
```

### Check Site Status
```bash
netlify status
```

### Open Site in Browser
```bash
netlify open:site
```

---

## Cost

Netlify Free Tier includes:
- ✅ 100GB bandwidth/month
- ✅ 300 build minutes/month
- ✅ Automatic HTTPS
- ✅ Global CDN
- ✅ Continuous deployment

Perfect for personal golf GPS use! 🎉

---

## Next Steps

1. **Deploy now**: Run `./deploy-netlify.sh`
2. **Test on phone**: Open the URL on your Android
3. **Bookmark it**: Add to home screen for quick access
4. **Go play golf**: Use it on the course! ⛳

---

## Support

- Netlify Docs: https://docs.netlify.com
- Netlify Support: https://answers.netlify.com
- Golf4us GPS Guide: See GPS_GUIDE.md

Happy golfing! 🏌️