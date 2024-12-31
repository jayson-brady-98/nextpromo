import json
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from itertools import cycle
import random

class ProxyManager:
    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.proxy_cycle = cycle(proxies)
        self.failed_proxies = set()
        
    def get_next_proxy(self) -> Optional[str]:
        for _ in range(len(self.proxies)):
            proxy = next(self.proxy_cycle)
            if proxy not in self.failed_proxies:
                return proxy
        return None
        
    def mark_proxy_failed(self, proxy: str):
        self.failed_proxies.add(proxy)
        
    def reset_failed_proxies(self):
        self.failed_proxies.clear()

def get_proxy_list() -> List[str]:
    return [
        'http://jvjqnbfh:0rf1ehf2nwpn@198.23.239.134:6540',
        'http://jvjqnbfh:0rf1ehf2nwpn@207.244.217.165:6712',
        'http://jvjqnbfh:0rf1ehf2nwpn@107.172.163.27:6543',
        'http://jvjqnbfh:0rf1ehf2nwpn@64.137.42.112:5157',
        'http://jvjqnbfh:0rf1ehf2nwpn@173.211.0.148:6641',
        'http://jvjqnbfh:0rf1ehf2nwpn@161.123.152.115:6360',
        'http://jvjqnbfh:0rf1ehf2nwpn@167.160.180.203:6754',
        'http://jvjqnbfh:0rf1ehf2nwpn@154.36.110.199:6853',
        'http://jvjqnbfh:0rf1ehf2nwpn@173.0.9.70:5653',
        'http://jvjqnbfh:0rf1ehf2nwpn@173.0.9.209:5792'
    ]

def get_promo_keywords() -> List[str]:
    return [
        'sale', '% off', 'discount', 'savings',
        'black friday', 'cyber monday',
        'summer sale', 'winter sale',
        'flash sale', 'eofy', 'end of financial year',
        'end of season', 'afterpay day',
        'boxing day', 'back to school sale',
        'promotion','clearance',  'march madness',
        'sale price', 'international women\'s day',
        'singles day', '% off everything', 'sitewide',
        'everything must go'
    ]

def is_in_navigation(element) -> bool:
    if not element or not hasattr(element, 'parent'):
        return False
    
    current = element
    depth = 0
    max_depth = 3
    
    while current and depth < max_depth:
        # Skip if current element is just a string
        if not hasattr(current, 'name'):
            current = current.parent
            depth += 1
            continue
            
        if current.name in ['nav']:
            return True
            
        # Only try to get classes if element is a Tag
        classes = []
        if hasattr(current, 'get'):
            classes = current.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
            
        nav_indicators = [
            'main-nav',
            'primary-nav', 
            'site-nav',
            'navbar',
            'main-menu',
            'primary-menu',
            'navigation-menu'
        ]
        
        if any(indicator in ' '.join(classes).lower() for indicator in nav_indicators):
            return True
            
        if hasattr(current, 'get') and current.get('role', '').lower() in ['navigation', 'menuitem']:
            return True
            
        current = current.parent
        depth += 1
        
    return False

def is_in_newsletter(element) -> bool:
    if not element or not hasattr(element, 'parent'):
        return False
        
    current = element
    while current:
        # Skip if current element is just a string
        if not hasattr(current, 'name'):
            current = current.parent
            continue
            
        if current.name in ['form', 'input']:
            return True
            
        # Only try to get classes if element is a Tag
        classes = []
        if hasattr(current, 'get'):
            classes = current.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
                
        newsletter_indicators = ['newsletter', 'subscribe', 'signup', 'form', 'mailing', 'contact-bar', 'contact-form', 'email-signup', 'popup']
        
        if hasattr(current, 'get'):
            if any(indicator in ' '.join(classes).lower() for indicator in newsletter_indicators):
                return True
            if any(indicator in current.get('id', '').lower() for indicator in newsletter_indicators):
                return True
                
        current = current.parent
    return False

def analyze_page_content(url: str, proxy_config: Dict) -> Tuple[bool, Dict[str, List[str]], Optional[str], bool]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        max_retries = 3
        retry_delay = 10
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    proxies=proxy_config,
                    timeout=30
                )
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text = ' '.join(soup.stripped_strings)
        text_lower = text.lower()
        
        # Add end date extraction
        end_date = extract_sale_end_date(text)
        
        keywords = get_promo_keywords()
        keyword_contexts = {}
        
        exclude_phrases = [
            'student discount',
            'military discount',
            'veterans discount',
            'pay with afterpay',
            'afterpay, pay',
            '10% student',
            '10% student',
            '10% military',
            '10% veterans',
            'refer a friend to earn',
            '100% composed of',
            '100% made of',
            '% off your first order',
            '% off when you',
            'for a chance to win'
        ]
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                contexts = []
                
                # Special handling for 'sale' keyword
                if keyword.lower() == 'sale':
                    # Find all text nodes containing 'sale'
                    for element in soup.find_all(string=re.compile(r'\bsale\b', re.I)):
                        if not is_in_navigation(element):
                            context_text = element.strip()
                            if context_text:
                                # Get surrounding text
                                context_start = max(0, text.lower().find(context_text.lower()) - 50)
                                context_end = min(len(text), text.lower().find(context_text.lower()) + len(context_text) + 50)
                                context = text[context_start:context_end].strip()
                                
                                # Apply existing exclusion rules
                                should_exclude = any(phrase in context.lower() for phrase in exclude_phrases)
                                if not should_exclude:
                                    if context_start > 0:
                                        context = f"...{context}"
                                    if context_end < len(text):
                                        context = f"{context}..."
                                    contexts.append(context)
                # Special handling for '% off' keyword
                elif '% off' in keyword.lower():
                    for element in soup.find_all(string=re.compile(r'\d+\s*%\s*off', re.I)):
                        if not is_in_navigation(element) and not is_in_newsletter(element):
                            context_text = element.strip()
                            if context_text:
                                context_start = max(0, text.lower().find(context_text.lower()) - 50)
                                context_end = min(len(text), text.lower().find(context_text.lower()) + len(context_text) + 50)
                                context = text[context_start:context_end].strip()
                                
                                should_exclude = any(phrase in context.lower() for phrase in exclude_phrases)
                                if not should_exclude:
                                    if context_start > 0:
                                        context = f"...{context}"
                                    if context_end < len(text):
                                        context = f"{context}..."
                                    contexts.append(context)
                else:
                    # Original keyword matching logic for other keywords
                    start = 0
                    while True:
                        index = text_lower.find(keyword.lower(), start)
                        if index == -1:
                            break
                            
                        context_start = max(0, index - 50)
                        context_end = min(len(text), index + len(keyword) + 50)
                        context = text[context_start:context_end].strip()
                        
                        # Keep the exclusion check
                        should_exclude = any(phrase in context.lower() for phrase in exclude_phrases)
                        if not should_exclude:
                            if context_start > 0:
                                context = f"...{context}"
                            if context_end < len(text):
                                context = f"{context}..."
                            contexts.append(context)
                        
                        start = index + 1
                
                if contexts:  # Only add if we have valid contexts after filtering
                    keyword_contexts[keyword] = contexts
        
        # Replace the current sitewide check with this more precise logic
        sitewide_patterns = [
            r'\d+%\s+off\s+everything',
            r'everything\s+\d+%\s+off',
            'black friday',
            'cyber monday',
            'sitewide',
            'everything must go'
        ]
        
        is_sitewide = False
        if keyword_contexts:
            for _, contexts in keyword_contexts.items():
                for context in contexts:
                    if any(re.search(pattern, context.lower()) for pattern in sitewide_patterns):
                        is_sitewide = True
                        break
                if is_sitewide:
                    break

        return bool(keyword_contexts), keyword_contexts, end_date, is_sitewide
        
    except Exception as e:
        print(f"Error analyzing {url}: {str(e)}")
        return False, {}, None, False

def batch_process_with_proxies(urls: List[str], from_date: str, to_date: str, 
                             proxies: List[str], batch_size: int = 5) -> Dict:
    proxy_manager = ProxyManager(proxies)
    all_results = {}
    
    for i in range(0, len(urls), batch_size):
        url_batch = urls[i:i + batch_size]
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            proxy = proxy_manager.get_next_proxy()
            if not proxy:
                print("All proxies have failed. Resetting failed proxies list...")
                proxy_manager.reset_failed_proxies()
                proxy = proxy_manager.get_next_proxy()
                
            try:
                print(f"Processing batch {i//batch_size + 1} using proxy: {proxy}")
                proxy_config = {'http': proxy, 'https': proxy}
                batch_results = get_wayback_urls(url_batch, from_date, to_date, proxy_config)
                all_results.update(batch_results)
                time.sleep(random.uniform(2, 5))
                break
                
            except requests.exceptions.RequestException as e:
                print(f"Proxy {proxy} failed: {str(e)}")
                proxy_manager.mark_proxy_failed(proxy)
                retry_count += 1
                
        if retry_count == max_retries:
            print(f"Failed to process batch after {max_retries} attempts")
            
    return all_results

def get_wayback_urls(urls: List[str], from_date: str, to_date: str, 
                    proxy_config: Optional[Dict] = None) -> Dict:
    wayback_api_url = "http://web.archive.org/cdx/search/cdx"
    available_urls = {}

    params = {
        "url": urls,
        "from": from_date,
        "to": to_date,
        "output": "json",
        "fl": "timestamp,original",
        "filter": ["statuscode:200"],
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    response = requests.get(
        wayback_api_url, 
        params=params, 
        headers=headers,
        proxies=proxy_config,
        timeout=30
    )
    
    data = response.json()
    
    for item in data[1:]:  # Skip header row
        timestamp, original_url = item
        url_dict = {
            'url': f"http://web.archive.org/web/{timestamp}/{original_url}",
            'original_url': original_url,
            'timestamp': timestamp,
            'promo_contexts': {},
            'promotion': False
        }
        available_urls[timestamp] = url_dict

    return available_urls

def group_snapshots_by_date(wayback_urls: dict) -> dict:
    daily_snapshots = defaultdict(list)
    for timestamp, data in wayback_urls.items():
        date = timestamp[:8]  # Extract YYYYMMDD
        daily_snapshots[date].append((timestamp, data))
    return daily_snapshots

def analyze_daily_snapshots(daily_snapshots: dict, proxies: List[str], completed_urls: set) -> dict:
    proxy_manager = ProxyManager(proxies)
    results = {}
    
    for date, snapshots in daily_snapshots.items():
        print(f"\nAnalyzing snapshots for date: {date}")
        
        for timestamp, data in snapshots:
            if timestamp in completed_urls:
                print(f"Skipping already processed {timestamp}...")
                results[timestamp] = data
                continue
            
            proxy = proxy_manager.get_next_proxy()
            if not proxy:
                proxy_manager.reset_failed_proxies()
                proxy = proxy_manager.get_next_proxy()
                
            proxy_config = {'http': proxy, 'https': proxy}
            print(f"Analyzing snapshot from {timestamp} using proxy: {proxy}")
            
            has_promo, keyword_contexts, end_date, is_sitewide = analyze_page_content(data['url'], proxy_config)
            data['promotion'] = has_promo
            data['promo_contexts'] = keyword_contexts
            data['sale_end_date'] = end_date
            data['sitewide'] = is_sitewide
            results[timestamp] = data
            
            completed_urls.add(timestamp)
            with open("checkpoint.json", "w") as f:
                json.dump(list(completed_urls), f)
            
            time.sleep(random.uniform(3, 7))
    
    return results

def extract_sale_end_date(text: str) -> str:
    # Time pattern components
    time_pattern = r'(?:\s+at)?\s*(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))?'
    timezone_pattern = r'(?:\s+[A-Z]{2,4}T)?(?:\s+[A-Z]{3})?'  # Matches EST, PDT, AEST, etc.
    
    # Patterns for different date formats with optional time and timezone
    patterns = [
        # Modified "Extended until/to" patterns
        rf'extended\s+(?:until|to)\s+(\w+day{time_pattern}{timezone_pattern})',
        rf'extended\s+(?:until|to)\s+(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        rf'(?:\s+\d{{4}})?{time_pattern}{timezone_pattern})',
        rf'extended\s+(?:until|to)\s+(\d{{1,2}}[/-]\d{{1,2}}(?:[/-]\d{{2,4}})?{time_pattern}{timezone_pattern})',
        
        # Days of week with optional time/timezone
        rf'(?:sale\s+)?ends?\s+(?:on\s+)?(\w+day{time_pattern}{timezone_pattern})',
        
        # Dates like "25th December" or "25 Dec 2024" with optional time/timezone
        rf'(?:sale\s+)?ends?\s+(?:on\s+)?(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        rf'(?:\s+\d{{4}})?{time_pattern}{timezone_pattern})',
        
        # Dates like DD/MM or DD/MM/YYYY with optional time/timezone
        rf'(?:sale\s+)?ends?\s+(?:on\s+)?(\d{{1,2}}[/-]\d{{1,2}}(?:[/-]\d{{2,4}})?{time_pattern}{timezone_pattern})',
        
        # Special days with optional time/timezone
        rf'(?:sale\s+)?ends?\s+(?:on\s+)?(\w+\s+day{time_pattern}{timezone_pattern})',
        
        # Time-specific patterns without dates
        rf'(?:sale\s+)?ends?\s+(?:at\s+)?(\d{{1,2}}(?::\d{{2}})?\s*(?:am|pm|a\.m\.|p\.m\.){timezone_pattern})',
        
        # Offer variants
        rf'offer\s+ends?\s+(?:on\s+)?(\w+day{time_pattern}{timezone_pattern})',
        rf'offer\s+ends?\s+(?:on\s+)?(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        rf'(?:\s+\d{{4}})?{time_pattern}{timezone_pattern})',
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Get the full match including time and timezone
            full_match = match.group(0)
            if full_match.lower().startswith(('sale', 'offer')):
                full_match = full_match.split(' ', 1)[1]  # Remove 'sale' or 'offer' prefix
            
            # Check if the match is not in navigation or newsletter
            soup_text = BeautifulSoup(text, 'html.parser')
            for element in soup_text.find_all(string=re.compile(re.escape(match.group(0)), re.IGNORECASE)):
                if not is_in_navigation(element) and not is_in_newsletter(element):
                    return full_match.strip()
    return ""

def main():
    urls = [
        "https://www.gymshark.com"
    ]
    from_date = "20130126"
    to_date = "20241230"
    
    # Get proxy list
    proxies = get_proxy_list()
    print(f"Loaded {len(proxies)} proxies")
    
    # Step 1: Batch fetch URLs from CDX API
    wayback_urls = batch_process_with_proxies(
        urls=urls,
        from_date=from_date,
        to_date=to_date,
        proxies=proxies,
        batch_size=5
    )
    
    print(f"Found {len(wayback_urls)} archived URLs")

    # Load checkpoint if exists
    try:
        with open("checkpoint.json", "r") as f:
            completed_urls = set(json.load(f))
    except FileNotFoundError:
        completed_urls = set()

    # Step 2: Group snapshots by date and analyze
    daily_snapshots = group_snapshots_by_date(wayback_urls)
    results = analyze_daily_snapshots(daily_snapshots, proxies, completed_urls)

    # Extract brand name from URL for filename
    brand_name = urls[0].replace('https://', '').replace('www.', '').split('.')[0]
    output_filename = f"{brand_name}Raw.json"

    # Write results with dynamic filename
    with open(output_filename, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    total_snapshots = len(results)
    promo_snapshots = sum(1 for data in results.values() if data['promotion'])
    skipped_snapshots = sum(1 for data in results.values() if data.get('skipped', False))
    
    print(f"\nAnalysis complete!")
    print(f"Total snapshots: {total_snapshots}")
    print(f"Snapshots with promotional content: {promo_snapshots}")
    print(f"Skipped snapshots (after finding daily promo): {skipped_snapshots}")
    print(f"Total requests made: {total_snapshots - skipped_snapshots}")

if __name__ == "__main__":
    main()