# 🎯 Event Registration System - Complete Guide

## 📋 Overview

This system allows you to:
1. **Admin**: Create golf events and generate registration links
2. **Members**: Self-register for events via a shared link
3. **Admin**: View registrations and manage participants
4. **Admin**: Enter scores (or let players enter their own)
5. **Everyone**: View results on the public results page

---

## 🚀 Quick Start for Admins

### Step 1: Create an Event

1. Open `event-registration-admin.html` in your browser
2. Fill in the event details:
   - **Event Name**: e.g., "April Monthly Challenge"
   - **Event Date**: Select the date
   - **Course Name**: e.g., "Deerfield Golf Course"
   - **Entry Fee**: Optional (leave 0 if free)
   - **Description**: Optional event details
   - **1:1:1 Contest**: Check if you want to enable the birdie contest

3. Click **"Create Event & Generate Registration Link"**

4. You'll get TWO important links:
   - **Registration Link**: Share this with members so they can register
   - **Admin Link**: Use this to manage the event and enter scores

### Step 2: Share Registration Link

Copy the registration link and share it via:
- WhatsApp
- Email
- Text message
- Social media

**Example message:**
```
🏌️ Golf Event Registration

Join us for the April Monthly Challenge!
📅 Date: April 30, 2026
⛳ Course: Deerfield Golf Course

Register here:
https://your-site.com/event-registration.html?event=event_123456

See you on the course! ⛳
```

### Step 3: Monitor Registrations

1. Go to the **"Manage Registrations"** tab
2. Select your event from the dropdown
3. View all registered players:
   - Total registrations
   - Who's participating in 1:1:1 contest
   - Handicaps
   - Registration timestamps

4. Export registrations to CSV if needed

---

## 👥 For Members (Players)

### How to Register

1. Click the registration link shared by the admin
2. You'll see the event details (name, date, course, etc.)
3. Fill in your information:
   - **Your Name**: Full name
   - **Golf Handicap**: Your official or estimated handicap
   - **1:1:1 Contest**: Check if you want to participate

4. Click **"Complete Registration"**
5. You'll see a confirmation message

**That's it!** You're registered for the event.

---

## 📊 Entering Scores (Two Options)

### Option 1: Players Enter Their Own Scores

**After the event, share this link with players:**
```
https://your-site.com/golf-ambassadors.html?event=event_123456
```

Players can:
1. Open the link
2. Select their name from the dropdown
3. Enter their scores hole-by-hole
4. Mark if they won the 1:1:1 contest
5. Submit their scorecard

### Option 2: Admin Enters Scores

**Admin can enter scores for any player:**

1. Open `event-registration-admin.html`
2. Go to **"Enter Scores"** tab
3. Select the event
4. Select the player
5. Enter:
   - Total score
   - Stableford points
   - Whether they won 1:1:1 contest
6. Click **"Save Score"**

**Note:** Admin entries override player entries if both exist.

---

## 🏆 Viewing Results

### Public Results Page

Share this link with everyone to view live results:
```
https://your-site.com/golf-ambassadors-results.html
```

The results page shows:
- Overall leaderboard
- Stableford points
- 1:1:1 contest winners
- Individual player details
- Real-time updates

---

## 📱 Mobile Access (Android/iPhone)

### For Admin:
1. Open `event-registration-admin.html` on your phone's browser
2. Create events and manage registrations on the go
3. Enter scores from the course

### For Members:
1. Click the registration link on your phone
2. Register in seconds
3. Enter scores after the round

**Pro Tip:** Add the pages to your home screen for quick access!

---

## 🔥 Complete Workflow Example

### Before the Event:

**Admin:**
1. Opens `event-registration-admin.html`
2. Creates event: "May Challenge - Deerfield GC"
3. Gets registration link
4. Shares link via WhatsApp group

**Members:**
1. Click registration link
2. Enter name and handicap
3. Confirm participation in 1:1:1 contest
4. Submit registration

**Admin:**
1. Monitors registrations in real-time
2. Exports list to CSV for records
3. Prepares scorecards

### During the Event:

**Players:**
- Play their round
- Track scores on paper or phone
- Try to win 1:1:1 contest (birdie on Par 3 with 2 clubs)

### After the Event:

**Option A - Players Enter Scores:**
1. Admin shares score entry link
2. Each player enters their own scores
3. Results update automatically

**Option B - Admin Enters Scores:**
1. Admin collects scorecards
2. Enters scores for all players
3. Marks 1:1:1 winners

**Everyone:**
- Views results on public results page
- Sees leaderboard rankings
- Checks 1:1:1 contest winners

---

## 💾 Data Storage

All data is stored locally in your browser using `localStorage`:
- Events
- Registrations
- Scores
- Results

**Important Notes:**
- Data persists across browser sessions
- Clearing browser data will delete all information
- For permanent storage, deploy to Firebase (see `DEPLOY_TO_FIREBASE_SIMPLE.md`)

---

## 🌐 Deploying to Firebase (Recommended)

To make your registration system accessible from any device:

1. Follow the guide in `DEPLOY_TO_FIREBASE_SIMPLE.md`
2. Deploy these files:
   - `event-registration-admin.html`
   - `event-registration.html`
   - `golf-ambassadors.html`
   - `golf-ambassadors-results.html`

3. Your URLs will be:
   - Admin: `https://your-app.web.app/event-registration-admin.html`
   - Registration: `https://your-app.web.app/event-registration.html?event=XXX`
   - Score Entry: `https://your-app.web.app/golf-ambassadors.html?event=XXX`
   - Results: `https://your-app.web.app/golf-ambassadors-results.html`

---

## 🎯 1:1:1 Contest Rules

**What is it?**
Make a birdie on any Par 3 hole using only 2 clubs to win!

**How it works:**
1. Player must register for the contest
2. During the round, if they make a birdie on a Par 3 using only 2 clubs, they win
3. Mark the achievement when entering scores
4. Winners are displayed on the results page

**Example:**
- Par 3, 150 yards
- Player uses driver and putter only
- Makes birdie (score of 2)
- Wins the 1:1:1 contest! 🏆

---

## 📊 Features Summary

### Admin Portal Features:
- ✅ Create unlimited events
- ✅ Generate unique registration links
- ✅ View real-time registrations
- ✅ Export registrations to CSV
- ✅ Enter scores for any player
- ✅ Manage multiple events simultaneously
- ✅ Track 1:1:1 contest participation

### Member Registration Features:
- ✅ Simple one-page registration
- ✅ Mobile-friendly design
- ✅ Instant confirmation
- ✅ No account required
- ✅ Handicap tracking
- ✅ 1:1:1 contest opt-in

### Score Entry Features:
- ✅ Player self-entry option
- ✅ Admin override capability
- ✅ Hole-by-hole scoring
- ✅ Stableford points calculation
- ✅ 1:1:1 contest tracking
- ✅ Real-time results updates

### Results Display Features:
- ✅ Live leaderboard
- ✅ Stableford rankings
- ✅ 1:1:1 contest winners
- ✅ Individual player stats
- ✅ Mobile-responsive design
- ✅ Auto-refresh capability

---

## 🔧 Troubleshooting

### "Event Not Found" Error
**Problem:** Registration link shows "Event Not Found"
**Solution:** 
- Make sure you're using the correct link
- Check that the event was created successfully
- Verify the event ID in the URL matches

### Registrations Not Showing
**Problem:** Admin can't see registrations
**Solution:**
- Refresh the page
- Select the correct event from dropdown
- Check browser console for errors
- Ensure localStorage is enabled

### Scores Not Saving
**Problem:** Scores don't save when submitted
**Solution:**
- Check internet connection (if using Firebase)
- Verify player is registered for the event
- Clear browser cache and try again
- Use admin score entry as backup

### Mobile Display Issues
**Problem:** Pages don't display correctly on mobile
**Solution:**
- Use Chrome or Safari browser
- Enable JavaScript
- Clear browser cache
- Try landscape orientation for tables

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review `GOLF_AMBASSADORS_HOW_TO_USE.md` for general usage
3. See `DEPLOY_TO_FIREBASE_SIMPLE.md` for hosting setup
4. Check browser console for error messages

---

## 🎉 Success Tips

1. **Test First**: Create a test event and register yourself before the real event
2. **Share Early**: Send registration links well before the event date
3. **Remind Players**: Send reminder messages a day before the event
4. **Backup Scores**: Keep paper scorecards as backup
5. **Check Results**: Verify all scores are entered correctly before finalizing
6. **Celebrate Winners**: Announce results promptly after the event

---

## 📱 WhatsApp Message Templates

### Registration Announcement:
```
🏌️ GOLF EVENT - REGISTER NOW!

Event: [Event Name]
📅 Date: [Date]
⛳ Course: [Course Name]
💰 Entry: $[Fee] (or FREE)

🎯 Special: 1:1:1 Contest!
Make a birdie on any Par 3 with only 2 clubs to win!

👉 REGISTER HERE:
[Registration Link]

Deadline: [Date]
See you on the course! ⛳
```

### Score Entry Reminder:
```
⛳ SCORES DUE!

Great round today! Please enter your scores:

📊 ENTER YOUR SCORES:
[Score Entry Link]

🏆 VIEW RESULTS:
[Results Link]

Please submit by [Time] today.
Thanks! 🏌️
```

### Results Announcement:
```
🏆 RESULTS ARE IN!

Congratulations to all participants!

VIEW FULL RESULTS:
[Results Link]

🥇 Winner: [Name]
🎯 1:1:1 Winner: [Name]

Thanks for playing! See you next time! ⛳
```

---

## 🎯 Best Practices

1. **Create Events in Advance**: Set up events at least a week before
2. **Close Registration**: Set a deadline (manually manage this)
3. **Verify Registrations**: Check the list before the event
4. **Collect Scores Promptly**: Get scores within 24 hours
5. **Publish Results Quickly**: Share results the same day
6. **Archive Events**: Keep records for future reference
7. **Backup Data**: Export registrations and scores to CSV

---

## 🚀 Ready to Start?

1. Open `event-registration-admin.html`
2. Create your first event
3. Share the registration link
4. Watch registrations come in!

**Good luck with your golf events! ⛳🏌️**