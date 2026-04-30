import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from io import StringIO
import sys

def get_golf_scorecard(course_name):
    # Better GolfLink search
    search_url = f"https://www.golflink.com/golf-courses/search?utf8=%E2%9C%93&q={course_name.replace(' ', '+')}"
    
    try:
        resp = requests.get(search_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        course_links = []
        for link in soup.find_all('a', href=re.compile(r'/golf-courses/')):
            if course_name.lower() in link.text.lower():
                url = "https://www.golflink.com" + link['href']
                course_links.append(url)
        
        if not course_links:
            print("No GolfLink match. Try official site.")
            return False
        
        # Try first match
        page_resp = requests.get(course_links[0])
        tables = pd.read_html(page_resp.text)
        
        for df in tables:
            df_str = df.to_string()
            if 'Par' in df_str and any(tee in df_str for tee in ['Blue','White','Gold','Red']):
                print(f"\n## {course_name} Scorecard [via GolfLink]")
                print(df.to_markdown(index=False))
                return True
        
        # Fallback: extract from page text
        soup = BeautifulSoup(page_resp.text, 'html.parser')
        scorecard_text = soup.get_text()
        par = re.search(r'par.*?(\d+)', scorecard_text, re.I)
        yards = re.findall(r'(\d{4})\s*yards?', scorecard_text)
        print(f"Course: {course_name}")
        print(f"Par: {par.group(1) if par else 'N/A'}")
        print(f"Yardages: {', '.join(yards[:4])} yds (top tees)")
        
    except Exception as e:
        print(f"Error: {e}")
    
    return False

if __name__ == "__main__":
    course = ' '.join(sys.argv[1:])
    get_golf_scorecard(course)
