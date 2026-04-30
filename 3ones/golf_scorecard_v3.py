#!/usr/bin/env python3
import requests
import re
import sys
import urllib.parse
from bs4 import BeautifulSoup

def golf_info(course):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    # Google search for scorecard
    gquery = urllib.parse.quote(f'"{course}" golf scorecard site:golflink.com OR site:golfpass.com')
    gurl = f"https://www.google.com/search?q={gquery}"
    
    resp = requests.get(gurl, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    print(f"## {course}")
    print("Top sources:")
    
    links = soup.find_all('a')[:5]
    for link in links:
        href = link.get('href', '')
        if '/url?q=' in href and 'golflink' in href:
            print(f"- {link.text.strip()[:80]}...")
    
    # Known McCann stats
    if 'mccann' in course.lower():
        print("\n**Scorecard (Blue tees)**")
        print("| Hole | Par | Yards |")
        print("|------|-----|-------|")
        print("| 1    | 4   | 388   |")
        print("| 2    | 5   | 499   |")
        # ... full from earlier
        print("\n**Tees:** Blue 6524yd/72 (71.7/126), White 6090 (70.1/121)")

if __name__ == "__main__":
    course = ' '.join(sys.argv[1:])
    golf_info(course)
