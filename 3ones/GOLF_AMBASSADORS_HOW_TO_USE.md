# 🏌️ GolfAmbassadors Portal - How to Use Guide

## 📋 Overview

The GolfAmbassadors system consists of **TWO portals**:

1. **Admin Portal** (`golf-ambassadors.html`) - For managing the competition
2. **Public Results Portal** (`golf-ambassadors-results.html`) - For viewing live results

---

## 🎯 STEP-BY-STEP USAGE GUIDE

### **STEP 1: Open the Admin Portal**

1. Open your web browser (Chrome, Safari, Firefox, Edge)
2. Navigate to: `golf-ambassadors.html`
3. You'll see 5 tabs at the top:
   - ⚙️ Setup
   - 👥 Participants  
   - 📊 Scorecard
   - 🏆 Results
   - 🔗 Share

---

### **STEP 2: Setup the Competition** (⚙️ Setup Tab)

1. **Enter Competition Name**
   - Example: "Monthly Golf Challenge - April 2026"

2. **Configure the Course**
   - Click "Add Hole" 18 times (for 18 holes)
   - For each hole, enter:
     - **Hole Number**: 1, 2, 3... 18
     - **Par**: 3, 4, or 5
     - **Handicap**: 1-18 (difficulty ranking)

3. **Set Entry Fee**
   - Example: 500 (for Ksh 500 per person)

4. Click **"Save Configuration"**

**💡 TIP:** You can also import course data from a JSON file if you have it saved.

---

### **STEP 3: Add Team Members** (👥 Participants Tab)

1. Click **"Add Player"** button
2. Fill in player details:
   - **Name**: Player's full name
   - **Handicap**: Their golf handicap (0-36)
   - **Participating**: Check this box ✅
   - **Paid**: Check when they've paid entry fee ✅

3. Repeat for all team members
4. Click **"Save Players"**

**Example:**
```
Name: John Doe
Handicap: 12
Participating: ✅
Paid: ✅
```

---

### **STEP 4: Enter Scores** (📊 Scorecard Tab)

**Option A: Individual Player Login (Recommended)**

1. Each player clicks **"Player Login"** button
2. Select their name from dropdown
3. Click **"Login"**
4. Enter their scores for each hole
5. Check **"2-Club"** box if they got a birdie (score of 2) on a Par 3 hole
6. Scores auto-save as they type

**Option B: Admin Entry**

1. Admin can enter scores for all players
2. Use the scorecard table
3. Enter score for each hole
4. Check 2-Club boxes where applicable

**💡 IMPORTANT:** 
- Scores must be entered for ALL 18 holes
- 2-Club achievements only count on Par 3 holes with a score of 2 (birdie)
- Scores save automatically to browser storage

---

### **STEP 5: View Results** (🏆 Results Tab)

The Results tab shows:

1. **📋 Hole-by-Hole Scorecard**
   - All players' scores for each hole
   - Green circles around 2-club achievements

2. **🏆 Overall Leaderboard**
   - Ranked by total Stableford points
   - Shows: Points, 2-Club count, Gross, Net, Winnings
   - Gold/Silver/Bronze highlighting for top 3

3. **🥇 Front 9 Leaderboard**
   - Ranked by front 9 points
   - Top 4 places win prizes

4. **🥈 Back 9 Leaderboard**
   - Ranked by back 9 points
   - Top 4 places win prizes

5. **💰 Prize Calculator**
   - Shows prize distribution
   - Can customize split percentages

6. **📊 Player Summary**
   - Shows only players with 2-club achievements
   - Lists handicap and hole numbers

---

### **STEP 6: Share Results** (🔗 Share Tab)

1. Click **"Open Public Results Page"** button
2. This opens `golf-ambassadors-results.html`
3. Share this page with your team:
   - Copy the URL from browser
   - Send via WhatsApp, Email, or SMS
   - Results update automatically every 30 seconds

**Public Portal Features:**
- ✅ Read-only (no one can change scores)
- ✅ Auto-refreshes every 30 seconds
- ✅ Shows all leaderboards
- ✅ Displays winnings per player
- ✅ Print-friendly
- ✅ Mobile responsive

---

## 🎮 TYPICAL WORKFLOW

### **Before the Round:**
1. Admin opens `golf-ambassadors.html`
2. Sets up competition (name, course, entry fee)
3. Adds all participating players
4. Shares public results link with team

### **During the Round:**
1. Each player logs in on their phone
2. Enters scores hole-by-hole as they play
3. Checks 2-Club box for Par 3 birdies
4. Team can view live results on public portal

### **After the Round:**
1. Admin verifies all scores are complete
2. Reviews leaderboards and prize distribution
3. Announces winners
4. Can export results (CSV, JSON, or Print)

---

## 💰 PRIZE DISTRIBUTION

### **Overall Competition (50/30/20 split):**
- 🥇 1st Place: 50% of total pot
- 🥈 2nd Place: 30% of total pot
- 🥉 3rd Place: 20% of total pot

### **Front 9 & Back 9 (40/30/20/10 split):**
- 🥇 1st Place: 40% of pot
- 🥈 2nd Place: 30% of pot
- 🥉 3rd Place: 20% of pot
- 🏅 4th Place: 10% of pot

**Example with 10 players @ Ksh 500 each:**
- Total Pot: Ksh 5,000
- Overall 1st: Ksh 2,500
- Overall 2nd: Ksh 1,500
- Overall 3rd: Ksh 1,000

---

## 📱 MOBILE USAGE

Both portals work perfectly on mobile devices:

1. **On Your Phone:**
   - Open browser (Chrome, Safari)
   - Navigate to the HTML file
   - Everything scales automatically
   - Touch-friendly buttons and inputs

2. **Player Score Entry:**
   - Login with your name
   - Scroll through holes
   - Tap to enter scores
   - Check 2-Club boxes easily

---

## 🔄 DATA PERSISTENCE

**How Data is Saved:**
- All data saves to **browser localStorage**
- Data persists even if you close the browser
- Both portals share the same data
- No internet connection required after loading

**To Clear Data:**
- Use browser developer tools
- Or start a new competition (overwrites old data)

---

## 🖨️ EXPORTING RESULTS

### **From Admin Portal:**
1. Go to Results tab
2. Click export buttons:
   - **CSV**: Download spreadsheet
   - **JSON**: Download data file
   - **Copy**: Copy to clipboard
   - **Print**: Print results

### **From Public Portal:**
1. Click **"🖨️ Print"** button
2. Use browser print dialog
3. Save as PDF or print to paper

---

## ❓ COMMON QUESTIONS

**Q: Can multiple people enter scores at the same time?**
A: Yes! Each player can log in and enter their own scores simultaneously.

**Q: What if someone makes a mistake?**
A: Simply re-enter the correct score. It will overwrite the old one.

**Q: Do we need internet?**
A: Only to initially load the pages. After that, everything works offline.

**Q: Can we use this for multiple competitions?**
A: Yes, but each new competition will overwrite the previous data. Export results before starting a new one.

**Q: What's a 2-Club achievement?**
A: Getting a birdie (score of 2) on a Par 3 hole. It's tracked separately for bragging rights!

**Q: How do handicaps work?**
A: The system automatically distributes handicap strokes across holes based on hole difficulty (handicap rating).

---

## 🆘 TROUBLESHOOTING

**Problem: Scores not showing on public portal**
- Solution: Make sure you saved scores in admin portal
- Refresh the public portal page

**Problem: Player can't log in**
- Solution: Make sure player is added in Participants tab with "Participating" checked

**Problem: 2-Club not counting**
- Solution: Must be Par 3 hole AND score must be exactly 2 (birdie)

**Problem: Winnings not calculating**
- Solution: Make sure entry fee is set and players are marked as "Paid"

---

## 📞 QUICK REFERENCE

### **Admin Portal URL:**
```
file:///path/to/golf-ambassadors.html
```

### **Public Portal URL:**
```
file:///path/to/golf-ambassadors-results.html
```

### **Key Shortcuts:**
- **Ctrl/Cmd + P**: Print results
- **F5**: Refresh page
- **Ctrl/Cmd + S**: Save (auto-saves anyway)

---

## 🎉 TIPS FOR SUCCESS

1. ✅ **Set up course before the round** - Don't rush during play
2. ✅ **Have players enter their own scores** - More accurate and engaging
3. ✅ **Share public link early** - Let everyone follow along
4. ✅ **Verify 2-Club achievements** - Only Par 3 birdies count
5. ✅ **Export results after** - Keep records of past competitions
6. ✅ **Use mobile devices** - Easier to enter scores on the course

---

## 🏆 ENJOY YOUR COMPETITION!

The GolfAmbassadors portal makes golf competitions transparent, fair, and fun for everyone. All scores are visible in real-time, and the automatic calculations ensure accurate results every time.

**Happy Golfing! ⛳**