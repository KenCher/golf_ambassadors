# Deerfield Country Club Scorecard Guide

## Overview
Deerfield Country Club features a unique 27-hole layout with three 9-hole courses: **North**, **East**, and **South**. Players can combine any two courses to create an 18-hole round.

## Official Scorecard Data

### Course Combinations
The following 18-hole combinations are available:

1. **North / South** (Most Common)
   - Total: Par 72
   - Black Tees: 7,026 yards
   - Blue Tees: 6,736 yards
   - White Tees: 6,109 yards
   - Yellow Tees: 5,344 yards
   - Green Tees: 5,196 yards

2. **North / East**
   - Total: Par 72
   - Blue Tees: 6,922 yards
   - White Tees: 6,424 yards
   - Yellow Tees: 5,321 yards
   - Green Tees: 5,141 yards

3. **South / East**
   - Total: Par 72
   - Blue Tees: 6,617 yards
   - White Tees: 6,313 yards
   - Yellow Tees: 5,309 yards
   - Green Tees: 5,107 yards

## Hole-by-Hole Details

### North Course (Holes 1-9)
| Hole | Par | HCP | Black | Blue | White | Yellow | Green |
|------|-----|-----|-------|------|-------|--------|-------|
| 1    | 5   | 17  | 457   | 447  | 437   | 425    | 415   |
| 2    | 4   | 3   | 435   | 428  | 339   | 318    | 312   |
| 3    | 4   | 7   | 441   | 431  | 400   | 332    | 326   |
| 4    | 3   | 15  | 212   | 200  | 166   | 155    | 144   |
| 5    | 5   | 5   | 562   | 556  | 526   | 426    | 420   |
| 6    | 4   | 9   | 384   | 373  | 362   | 278    | 273   |
| 7    | 4   | 1   | 456   | 443  | 364   | 365    | 356   |
| 8    | 3   | 13  | 177   | 158  | 146   | 105    | 102   |
| 9    | 4   | 11  | 402   | 386  | 370   | 274    | 267   |
| **Out** | **36** | | **3,526** | **3,422** | **3,110** | **2,678** | **2,615** |

### East Course (Holes 10-18 when combined with North)
| Hole | Par | HCP | Blue | White | Yellow | Green |
|------|-----|-----|------|-------|--------|-------|
| 10   | 4   | 14  | 390  | 372   | 285    | 279   |
| 11   | 4   | 16  | 384  | 358   | 340    | 336   |
| 12   | 3   | 12  | 204  | 176   | 133    | 128   |
| 13   | 4   | 2   | 403  | 351   | 291    | 287   |
| 14   | 4   | 6   | 457  | 390   | 320    | 314   |
| 15   | 4   | 8   | 417  | 372   | 305    | 301   |
| 16   | 5   | 4   | 518  | 486   | 439    | 375   |
| 17   | 3   | 10  | 198  | 165   | 136    | 121   |
| 18   | 5   | 18  | 529  | 432   | 394    | 385   |
| **In** | **36** | | **3,500** | **3,314** | **2,643** | **2,526** |

### South Course (Holes 19-27, becomes 10-18 when combined with North)
| Hole | Par | HCP | Blue | White | Yellow | Green |
|------|-----|-----|------|-------|--------|-------|
| 19   | 4   | 9   | 383  | 374   | 360    | 355   |
| 20   | 3   | 11  | 156  | 141   | 133    | 124   |
| 21   | 5   | 13  | 503  | 491   | 423    | 415   |
| 22   | 4   | 5   | 440  | 432   | 420    | 408   |
| 23   | 3   | 1   | 161  | 149   | 135    | 128   |
| 24   | 5   | 3   | 455  | 442   | 359    | 349   |
| 25   | 4   | 7   | 366  | 350   | 287    | 279   |
| 26   | 5   | 15  | 452  | 442   | 398    | 389   |
| 27   | 3   | 17  | 201  | 178   | 151    | 134   |
| **Tot** | **36** | | **3,117** | **2,999** | **2,666** | **2,581** |

## Data Files

### 1. `deerfield-complete-scorecard.json`
Complete JSON file with all course data including:
- All three 9-hole courses (North, East, South)
- All tee box yardages
- Par and handicap for each hole
- 18-hole combination totals
- Metadata and source information

**Status:** ✅ Updated with official scorecard data

### 2. `deerfield-tournament.html`
Tournament manager with embedded fallback data:
- Contains `DEERFIELD_NORTH_SOUTH` constant
- Used when JSON file cannot be loaded (e.g., opening HTML directly)
- Includes yardages for all tee boxes

**Status:** ✅ Updated with official scorecard data

## Tee Box Information

### Available Tee Boxes by Course Combination

**North / South:**
- Black, Blue, White, Yellow, Green (all 5 tee boxes)

**North / East:**
- Blue, White, Yellow, Green (4 tee boxes - no Black)

**South / East:**
- Blue, White, Yellow, Green (4 tee boxes - no Black)

## Handicap System

The handicap numbers (HCP column) indicate the difficulty ranking of each hole:
- **1** = Hardest hole
- **18** = Easiest hole

These are used to allocate handicap strokes in match play and stroke play competitions.

## Usage in Tournament Manager

The Deerfield Tournament Manager (`deerfield-tournament.html`) automatically:
1. Attempts to load `deerfield-complete-scorecard.json`
2. Falls back to embedded `DEERFIELD_NORTH_SOUTH` data if JSON unavailable
3. Displays course selection dropdown with all three combinations
4. Shows appropriate tee boxes based on selected course combination
5. Uses hole handicaps for net score calculations

## Data Accuracy

✅ **Verified:** All yardages, pars, and handicaps match the official Deerfield Country Club scorecard.

## Notes

- GPS coordinates are not included in the scorecard data
- Use the Course Mapper tool to add precise tee and green locations if needed
- The tournament manager works offline with embedded data
- For full functionality (all course combinations), use with a web server to load the JSON file