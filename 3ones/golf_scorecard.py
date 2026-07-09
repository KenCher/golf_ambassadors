#!/usr/bin/env python3
"""
Golf Scorecard Finder - Enhanced Version
Supports search + known courses with full hole-by-hole data
Usage: python golf_scorecard.py "Course Name"
"""

import requests
import re
import sys
import urllib.parse
from bs4 import BeautifulSoup
import json

KNOWN_COURSES = {
    "mccann memorial golf course": {
        "par": 72,
        "tees": {
            "Blue": {"yards": 6524, "rating": 71.7, "slope": 126},
            "White": {"yards": 6090, "rating": 70.1, "slope": 121},
            "Gold": {"yards": 5617, "rating": 67.9, "slope": 117},
            "Red": {"yards": 5315, "rating": 70.4, "slope": 117}
        },
        "holes": {
            "par": [4,5,4,5,3,4,4,3,4, 4,4,3,4,5,3,4,5,4],
            "blue": [388,499,429,491,184,317,333,149,393, 401,399,188,411,548,143,353,475,423]
        }
    },
    "casperkill golf club": {
        "par": 72,
        "tees": {
            "Blue": {"yards": 6690},
            "White": {"yards": 6153},
            "Gold": {"yards": 5599},
            "Red": {"yards": 4868}
        },
        "holes": {
            "par": [5,4,3,4,5,4,4,3,4, 5,4,3,4,4,4,3,4,5],
            "blue": [508,416,204,331,536,338,396,179,353, 511,445,208,417,357,393,182,425,491]
        }
    }
    # Add more courses here
}

def print_scorecard(course_data):
    print(f"\n## Tee Summary")
    print("| Tee  | Yards | Rating | Slope |")
    print("|------|-------|--------|-------|")
    for tee, info in course_data["tees"].items():
        rating = info.get("rating", "N/A")
        slope = info.get("slope", "N/A")
        print(f"| {tee:<4} | {info['yards']:>5} | {rating:>6} | {slope:>5} |")
    
    print("\n## Hole-by-Hole (Blue Tees)")
    print("| Hole | Par | Yards |")
    print("|------|-----|-------|")
    for i, (p, y) in enumerate(zip(course_data["holes"]["par"], course_data["holes"]["blue"]), 1):
        print(f"| {i:>4} | {p:>3} | {y:>5} |")

def search_web(course):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    query = urllib.parse.quote(f'"{course}" golf scorecard')
    url = f"https://www.google.com/search?q={query}"
    
    try:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        print("🔍 Web sources:")
        links = soup.find_all('a', href=re.compile(r'/(url\?q=|search\?)'))[:3]
        for link in links:
            href = link.get('href', '')
            if any(site in href for site in ['golflink.com', 'golfpass.com', 'mscorecard.com']):
                print(f"- {link.get_text(strip=True)[:70]}...")
    except:
        pass

def main(course_name):
    course_key = course_name.lower()
    found = False
    
    # Check known courses
    for key, data in KNOWN_COURSES.items():
        if key in course_key:
            print(f"✅ Found {course_name}")
            print_scorecard(data)
            found = True
            break
    
    if not found:
        print("❌ No exact match. Searching web...")
        search_web(course_name)
        print("\n💡 Tip: Add to script or visit official site.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python golf_scorecard.py \"Course Name\"")
        sys.exit(1)
    
    course = ' '.join(sys.argv[1:])
    main(course)
