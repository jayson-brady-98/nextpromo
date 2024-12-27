import json
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Tuple
import random

def get_promo_keywords() -> List[str]:
    return [
        'sale', 
        'off',
        'discount',
        'save',
        'black friday',
        'cyber monday',
        'summer sale',
        'winter sale',
        'flash sale',
        'eofy',
        'end of financial year',
        'end of season',
        'afterpay day',
        'promotion',
        'deal',
        'clearance',
        'outlet',
        '%',
        'special offer'
    ]

def analyze_page_content(url: str) -> Tuple[bool, Dict[str, List[str]]]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get visible text content
        text = ' '.join(soup.stripped_strings)
        text_lower = text.lower()
        
        # Check for keywords and capture context
        keywords = get_promo_keywords()
        keyword_contexts = {}
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                # Find all occurrences of the keyword
                contexts = []
                start = 0
                while True:
                    index = text_lower.find(keyword.lower(), start)
                    if index == -1:
                        break
                        
                    # Capture surrounding context (50 chars before and after)
                    context_start = max(0, index - 50)
                    context_end = min(len(text), index + len(keyword) + 50)
                    context = text[context_start:context_end].strip()
                    
                    # Add ellipsis if we truncated the context
                    if context_start > 0:
                        context = f"...{context}"
                    if context_end < len(text):
                        context = f"{context}..."
                        
                    contexts.append(context)
                    start = index + 1
                
                if contexts:
                    keyword_contexts[keyword] = contexts
                
        return bool(keyword_contexts), keyword_contexts
        
    except Exception as e:
        print(f"Error analyzing {url}: {str(e)}")
        return False, {}

def get_wayback_urls(urls, from_date, to_date):
    wayback_api_url = "http://web.archive.org/cdx/search/cdx"
    available_urls = {}

    for url in urls:
        params = {
            "url": url,
            "from": from_date,
            "to": to_date,
            "output": "json",
            "fl": "timestamp,original",
            "filter": ["statuscode:200"],
        }
        response = requests.get(wayback_api_url, params=params)

        if response.status_code != 200:
            print(f"Warning: Received status code {response.status_code} from Wayback for {url}")
            continue

        data = response.json()

        url_dict = {
            item[0]: {
                'url': f"http://web.archive.org/web/{item[0]}/{item[1]}",
                'original_url': item[1],
                'timestamp': item[0],
                'promo_contexts': {},
                'y': 0
            }
            for item in data[1:]
        }

        available_urls.update(url_dict)

    return available_urls

def main():
    urls = [
        "https://www.gymshark.com",
    ]
    from_date = "20230101"  # YYYYMMDD
    to_date = "20241227"    # YYYYMMDD
    
    # Get archived URLs
    wayback_urls = get_wayback_urls(urls, from_date, to_date)
    print(f"Found {len(wayback_urls)} archived URLs")

    # Load checkpoint if exists
    try:
        with open("checkpoint.json", "r") as f:
            completed_urls = set(json.load(f))
    except FileNotFoundError:
        completed_urls = set()

    for timestamp, data in wayback_urls.items():
        if timestamp in completed_urls:
            print(f"Skipping already processed {timestamp}...")
            continue
            
        print(f"Analyzing snapshot from {timestamp}...")
        has_promo, keyword_contexts = analyze_page_content(data['url'])
        data['y'] = 1 if has_promo else 0
        data['promo_contexts'] = keyword_contexts
        
        # Save progress
        completed_urls.add(timestamp)
        with open("checkpoint.json", "w") as f:
            json.dump(list(completed_urls), f)
            
        delay = random.uniform(3, 7)
        time.sleep(delay)

    # Write the results to a JSON file
    with open("promo_analysis.json", "w") as f:
        json.dump(wayback_urls, f, indent=2)

    # Print summary
    promo_snapshots = sum(1 for data in wayback_urls.values() if data['y'] == 1)
    print(f"\nAnalysis complete!")
    print(f"Total snapshots: {len(wayback_urls)}")
    print(f"Snapshots with promotional content: {promo_snapshots}")

if __name__ == "__main__":
    main()