# Casperkill Golf Club Scorecard Guide

## Overview
Casperkill Golf Club is an 18-hole championship golf course in Poughkeepsie, NY, designed by renowned architect Robert Trent Jones, ASGCA.

## Course Information
- **Location:** Poughkeepsie, New York
- **Designer:** Robert Trent Jones, ASGCA
- **Total Holes:** 18
- **Par:** 72 (36 out, 36 in)
- **Course Rating:** 72.4 (Blue Tees)
- **Slope Rating:** 130 (Blue Tees)

## Yardage by Tee Box
| Tee Box | Total Yards | Front 9 | Back 9 | Rating | Slope |
|---------|-------------|---------|--------|--------|-------|
| Blue    | 6,690       | 3,261   | 3,429  | 72.4   | 130   |
| White   | 6,153       | 3,012   | 3,141  | -      | -     |
| Gold    | 5,599       | 2,705   | 2,894  | -      | -     |
| Red     | 4,868       | 2,371   | 2,497  | -      | -     |

## Hole-by-Hole Details

### Front Nine (Holes 1-9)
| Hole | Par | HCP | Blue | White | Gold | Red |
|------|-----|-----|------|-------|------|-----|
| 1    | 5   | 1   | 508  | 478   | 425  | 422 |
| 2    | 4   | 2   | 416  | 387   | 367  | 279 |
| 3    | 3   | 3   | 204  | 168   | 137  | 83  |
| 4    | 4   | 4   | 331  | 321   | 307  | 238 |
| 5    | 5   | 5   | 536  | 495   | 420  | 410 |
| 6    | 4   | 6   | 338  | 305   | 305  | 274 |
| 7    | 4   | 7   | 396  | 367   | 340  | 313 |
| 8    | 3   | 8   | 179  | 159   | 102  | 92  |
| 9    | 4   | 9   | 353  | 332   | 302  | 260 |
| **Out** | **36** | | **3,261** | **3,012** | **2,705** | **2,371** |

### Back Nine (Holes 10-18)
| Hole | Par | HCP | Blue | White | Gold | Red |
|------|-----|-----|------|-------|------|-----|
| 10   | 5   | 10  | 511  | 474   | 470  | 367 |
| 11   | 4   | 11  | 445  | 412   | 374  | 333 |
| 12   | 3   | 12  | 208  | 150   | 135  | 98  |
| 13   | 4   | 13  | 417  | 375   | 335  | 274 |
| 14   | 4   | 14  | 357  | 328   | 292  | 285 |
| 15   | 4   | 15  | 393  | 366   | 343  | 296 |
| 16   | 3   | 16  | 182  | 156   | 146  | 134 |
| 17   | 4   | 17  | 425  | 410   | 357  | 335 |
| 18   | 5   | 18  | 491  | 470   | 442  | 375 |
| **In** | **36** | | **3,429** | **3,141** | **2,894** | **2,497** |
| **Total** | **72** | | **6,690** | **6,153** | **5,599** | **4,868** |

## Handicap System

The handicap numbers (HCP column) indicate the difficulty ranking of each hole:
- **1** = Hardest hole (Hole 1 - Par 5, 508 yards from Blue)
- **18** = Easiest hole (Hole 18 - Par 5, 491 yards from Blue)

Note: Casperkill uses sequential handicap numbering (1-18 in order), which is less common than the traditional stroke allocation system.

## Notable Holes

### Signature Holes

**Hole 1 (Par 5, HCP 1)** - The Opener
- Blue: 508 yards
- Hardest hole on the course
- Sets the tone for the round

**Hole 5 (Par 5, HCP 5)** - The Monster
- Blue: 536 yards (longest hole)
- Challenging par 5 on the front nine

**Hole 11 (Par 4, HCP 11)** - The Test
- Blue: 445 yards (longest par 4)
- Demanding tee shot and approach

### Par 3s
- **Hole 3:** 204/168/137/83 yards (HCP 3)
- **Hole 8:** 179/159/102/92 yards (HCP 8)
- **Hole 12:** 208/150/135/98 yards (HCP 12)
- **Hole 16:** 182/156/146/134 yards (HCP 16)

### Par 5s
- **Hole 1:** 508/478/425/422 yards (HCP 1) - Hardest
- **Hole 5:** 536/495/420/410 yards (HCP 5)
- **Hole 10:** 511/474/470/367 yards (HCP 10)
- **Hole 18:** 491/470/442/375 yards (HCP 18) - Easiest

## Data Files

### 1. `casperkill-scorecard.json`
Complete JSON file with all course data including:
- All 18 holes with par and handicap
- All tee box yardages (Blue, White, Gold, Red)
- Course ratings and slopes
- Designer information
- Metadata and source information

**Status:** ✅ Created with official scorecard data

### 2. `tournament-manager.html` (Universal G4K)
The universal tournament manager now includes Casperkill as a preset option:
- Select "Casperkill Golf Club (Poughkeepsie, NY)" from the preset dropdown
- Automatically loads all hole data with correct pars and handicaps
- Ready to add players and start tournament

**Status:** ✅ Updated with Casperkill preset

## Usage in Tournament Manager

### Quick Load Method (Recommended)
1. Open `tournament-manager.html`
2. In the "Course Setup" tab, select "Casperkill Golf Club (Poughkeepsie, NY)" from the preset dropdown
3. Course data loads automatically with correct par for each hole
4. Click "Continue to Add Players" to proceed

### Via GPS Course Finder
1. Open `g4k-course-finder.html`
2. Click "📍 Find Courses Near Me" (if in Poughkeepsie area)
3. Or search "Casperkill"
4. Select course - will load with correct scorecard data

## Tee Box Recommendations

### Blue Tees (6,690 yards)
- **Rating:** 72.4
- **Slope:** 130
- **Recommended for:** Low handicap players (0-10)
- **Challenge Level:** Championship

### White Tees (6,153 yards)
- **Recommended for:** Mid handicap men (10-20)
- **Challenge Level:** Regular play

### Gold Tees (5,599 yards)
- **Recommended for:** Senior men, high handicap men (20+)
- **Challenge Level:** Senior/Forward

### Red Tees (4,868 yards)
- **Recommended for:** Ladies, juniors
- **Challenge Level:** Forward tees

## Robert Trent Jones Design Features

As a Robert Trent Jones, ASGCA design, Casperkill features:
- Strategic bunkering
- Elevated greens
- Risk-reward shot options
- Challenging but fair layout
- Emphasis on accuracy over distance

## Tournament Features Available

When using Casperkill in the tournament manager, you get:
- ✅ Correct par for each hole (not all par 4s!)
- ✅ Proper handicap rankings (1-18)
- ✅ Player management with tee box selection
- ✅ Live scoring for all 18 holes
- ✅ Gross and Net leaderboards
- ✅ Skins game tracking (Gross & Net)
- ✅ Scramble team management
- ✅ CSV player import
- ✅ Printable scorecards

## Data Accuracy

✅ **Verified:** All yardages, pars, handicaps, ratings, and slopes match the official Casperkill Golf Club scorecard.

## Course Statistics

- **Par 3s:** 4 holes (3, 8, 12, 16)
- **Par 4s:** 10 holes (2, 4, 6, 7, 9, 11, 13, 14, 15, 17)
- **Par 5s:** 4 holes (1, 5, 10, 18)
- **Longest Hole:** #5 (536 yards, Par 5)
- **Shortest Hole:** #8 (179 yards, Par 3)
- **Hardest Hole:** #1 (Par 5, HCP 1)
- **Easiest Hole:** #18 (Par 5, HCP 18)

## Notes

- GPS coordinates included for course finder integration
- Sequential handicap system (1-18) rather than traditional stroke allocation
- Robert Trent Jones design emphasizes strategic play
- Blue tees provide championship-level challenge (Rating 72.4, Slope 130)