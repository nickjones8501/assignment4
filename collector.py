import requests
from bs4 import BeautifulSoup
import os
from pathlib import Path

def scrape_chickfila_menu():
    """Scrape Chick-fil-A menu data from their website"""
    url = "https://www.chick-fil-a.com/menu/sides"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract main content - this will need adjustment based on actual page structure
        main_content = soup.find('main') or soup.find('div', class_='main-content') or soup.body
        
        # Remove script and style elements
        for script in main_content(["script", "style"]):
            script.decompose()
        
        # Get clean text
        text_blob = main_content.get_text(separator='\n', strip=True)
        
        # Save to file
        Path("data").mkdir(exist_ok=True)
        with open("data/raw_blob.txt", "w", encoding="utf-8") as f:
            f.write(text_blob)
        
        print(f"Scraped {len(text_blob)} characters from {url}")
        return text_blob
        
    except Exception as e:
        print(f"Error scraping website: {e}")
        return None

if __name__ == "__main__":
    blob = scrape_chickfila_menu()
    if blob:
        print("Menu data extracted successfully!")