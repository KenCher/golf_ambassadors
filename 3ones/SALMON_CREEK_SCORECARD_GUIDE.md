# Salmon Creek Country Club Scorecard Guide

## Overview
Salmon Creek Country Club is a traditional 18-hole golf course with three tee options: White, Gold, and Red.

## Official Scorecard Data

### Course Information
- **Total Holes:** 18
- **Par:** 72 (36 out, 36 in)
- **Course Rating & Slope:**
  - White Tees: 71.0 / 128 (Men's)
  - Gold Tees: 67.1 / 117 (Men's)
  - Red Tees: 73.8 / 121 (Ladies)

### Yardage by Tee Box
| Tee Box | Total Yards | Front 9 | Back 9 |
|---------|-------------|---------|--------|
| White   | 6,430       | 3,455   | 2,975  |
| Gold    | 5,690       | 3,010   | 2,680  |
| Red     | 5,470       | 2,905   | 2,565  |

## Hole-by-Hole Details

### Front Nine (Holes 1-9)
| Hole | Par | HCP | White | Gold | Red |
|------|-----|-----|-------|------|-----|
| 1    | 4   | 9   | 325   | 305  | 315 |
| 2    | 5   | 15  | 495   | 390  | 350 |
| 3    | 4   | 7   | 395   | 365  | 345 |
| 4    | 3   | 13  | 185   | 135  | 155 |
| 5    | 4   | 3   | 455   | 400  | 375 |
| 6    | 4   | 17  | 345   | 290  | 345 |
| 7    | 4   | 5   | 465   | 400  | 365 |
| 8    | 4   | 11  | 360   | 360  | 320 |
| 9    | 4   | 1   | 430   | 365  | 335 |
| **Out** | **36** | | **3,455** | **3,010** | **2,905** |

### Back Nine (Holes 10-18)
| Hole | Par | HCP | White | Gold | Red |
|------|-----|-----|-------|------|-----|
| 10   | 3   | 18  | 175   | 145  | 150 |
| 11   | 4   | 2   | 415   | 390  | 380 |
| 12   | 5   | 4   | 505   | 400  | 390 |
| 13   | 4   | 10  | 295   | 295  | 270 |
| 14   | 5   | 8   | 515   | 425  | 380 |
| 15   | 4   | 16  | 285   | 285  | 285 |
| 16   | 3   | 14  | 165   | 155  | 155 |
| 17   | 4   | 12  | 295   | 285  | 250 |
| 18   | 4   | 6   | 325   | 300  | 305 |
| **In** | **36** | | **2,975** | **2,680** | **2,565** |
| **Total** | **72** | | **6,430** | **5,690** | **5,470** |

## Handicap System

The handicap numbers (HCP column) indicate the difficulty ranking of each hole:
- **1** = Hardest hole (Hole 9)
- **18** = Easiest hole (Hole 10)

These are used to allocate handicap strokes in match play and stroke play competitions.

## Notable Holes

### Hardest Holes (Handicap 1-3)
1. **Hole 9** (Par 4, HCP 1) - The signature hole and toughest on the course
   - White: 430 yards
   - Gold: 365 yards
   - Red: 335 yards

2. **Hole 11** (Par 4, HCP 2) - Long par 4 on the back nine
   - White: 415 yards
   - Gold: 390 yards
   - Red: 380 yards

3. **Hole 5** (Par 4, HCP 3) - Challenging mid-length par 4
   - White: 455 yards
   - Gold: 400 yards
   - Red: 375 yards

### Par 3s
- Hole 4: 185/135/155 yards (HCP 13)
- Hole 10: 175/145/150 yards (HCP 18) - Easiest hole
- Hole 16: 165/155/155 yards (HCP 14)

### Par 5s
- Hole 2: 495/390/350 yards (HCP 15)
- Hole 12: 505/400/390 yards (HCP 4)
- Hole 14: 515/425/380 yards (HCP 8)

## Data Files

### 1. `salmon-creek-scorecard.json`
Complete JSON file with all course data including:
- All 18 holes with par and handicap
- All tee box yardages (White, Gold, Red)
- Course ratings and slopes
- Metadata and source information

**Status:** ✅ Created with official scorecard data

### 2. `tournament-manager.html` (Universal G4K)
The universal tournament manager now includes Salmon Creek as a preset option:
- Select "Salmon Creek Country Club" from the preset dropdown
- Automatically loads all hole data
- Ready to add players and start tournament

**Status:** ✅ Updated with Salmon Creek preset

## Usage in Tournament Manager

### Quick Load Method (Recommended)
1. Open `tournament-manager.html`
2. In the "Course Setup" tab, select "Salmon Creek Country Club" from the preset dropdown
3. Course data loads automatically
4. Click "Continue to Add Players" to proceed

### Manual Entry Method
1. Open `tournament-manager.html`
2. Select "18 Holes"
3. Click "Enter Custom Hole Data"
4. Enter par and handicap for each hole manually

## Tee Box Recommendations

### White Tees (6,430 yards)
- **Rating:** 71.0
- **Slope:** 128
- **Recommended for:** Low to mid handicap men (0-18)

### Gold Tees (5,690 yards)
- **Rating:** 67.1
- **Slope:** 117
- **Recommended for:** Senior men, high handicap men (18+)

### Red Tees (5,470 yards)
- **Rating:** 73.8
- **Slope:** 121
- **Recommended for:** Ladies, juniors

## Tournament Features Available

When using Salmon Creek in the tournament manager, you get:
- ✅ Player management with handicaps
- ✅ Live scoring for all 18 holes
- ✅ Gross and Net leaderboards
- ✅ Skins game tracking (Gross & Net)
- ✅ Scramble team management
- ✅ CSV player import
- ✅ Printable scorecards
- ✅ Real-time standings

## Data Accuracy

✅ **Verified:** All yardages, pars, handicaps, ratings, and slopes match the official Salmon Creek Country Club scorecard.

## Notes

- GPS coordinates are not included in the scorecard data
- Use the Course Mapper tool to add precise tee and green locations if needed
- The tournament manager works offline with embedded data
- For the dedicated Salmon Creek experience, use the preset option in the universal manager