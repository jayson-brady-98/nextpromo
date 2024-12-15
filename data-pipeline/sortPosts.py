import csv
import re
from datetime import datetime
import os

# Function to filter Instagram posts for sales information
def filter_sales_posts(posts):
    # More specific sale-related patterns using regex
    sale_patterns = [
        r'(?i)(?<!not a\s)(?:flash |huge |big )?sale\b',  # excludes "not a sale"
        r'(?i)(?<!not on\s)(?:flash |huge |big )?sale\b',  # excludes "not on sale"
        r'(?i)\b\d+%\s*off\b',  # percentage discounts
        r'(?i)\bclearance\b',
        r'(?i)\bpromo(?:tion)?\s+code[:\s]\s*[A-Z0-9]+\b',  # promo codes with actual code
        r'(?i)\bspecial\s+offer\b',
        r'(?i)\bdiscount\s+(?:code|price)',
        r'(?i)\bdeals?\b',  # Match "deals" on its own
        r'(?i)\bcyber\s+monday\b'  # Match "cyber monday" on its own
    ]
    
    date_patterns = [
        r'(?i)\b(?:\d{1,2}(?:st|nd|rd|th)? )?(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(?:st|nd|rd|th)?\b',
        r'(?i)\b\d{1,2}(?:st|nd|rd|th)? (January|February|March|April|May|June|July|August|September|October|November|December)\b',
        r'(?i)\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
    ]
    
    # Add sitewide patterns
    sitewide_patterns = [
        r'(?i)\bsitewide\b',
        r'(?i)\d+%\s+off\s+everything\b',
        r'(?i)\bentire\s+site\b'
    ]
    
    # Add event patterns
    event_patterns = [
        r'(?i)\bblack\s+friday\b',
        r'(?i)\bcyber\s+monday\b',
        r'(?i)\bchristmas(?:\s+day)?\b',
        r'(?i)\bafterp(?:ay)?\s+day\b',
        r'(?i)\bboxing\s+day\b',
        r'(?i)\bmother(?:\'s)?\s+day\b',
        r'(?i)\bfather(?:\'s)?\s+day\b',
        r'(?i)\beaster\b',
        r'(?i)\bvalentine(?:\'s)?\s+day\b',
        r'(?i)\bsingles\s+day\b',
        r'(?i)\bmarch\s+madness\b',
        r'(?i)\beo?fy\b',  # Matches both EOFY and end of financial year
        r'(?i)\bend\s+of\s+financial\s+year\b'
    ]
    
    # Extract sale details from posts
    result = []
    for post in posts:
        # Check if the post mentions sales using the new patterns
        is_sale_post = any(re.search(pattern, post['caption'].lower()) for pattern in sale_patterns)
        
        # Extract the year from the post_date
        post_date_str = post.get('post_date', 'N/A')
        post_year = None
        if post_date_str != 'N/A':
            try:
                post_date = datetime.fromisoformat(post_date_str.replace("Z", "+00:00"))
                post_year = post_date.year
                post_date_str = post_date.strftime('%d-%m-%Y')  # Format post_date as DD-MM-YYYY
            except ValueError:
                post_year = None
        
        # Initialize sale_date and sale_discount
        sale_date = 'N/A'
        sale_discount = 'N/A'
        
        if is_sale_post:
            # Check for "current sale" indicators
            current_sale_patterns = [
                r'\b(?:now|currently|today)\b',
                r'\bon\s+now\b',
                r'\bhappening\s+now\b',
                r'\bgoing\s+on\b'
            ]
            
            is_current_sale = any(re.search(pattern, post['caption'].lower()) for pattern in current_sale_patterns)
            
            # Find the sale date in the caption
            date_found = False
            for pattern in date_patterns:
                date_match = re.search(pattern, post['caption'])
                if date_match:
                    sale_date_str = date_match.group()
                    # If the date is in "Month Day" or "Day Month" format
                    if re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', sale_date_str):
                        if post_year:
                            # Remove date suffixes (both lower and uppercase)
                            sale_date_str = re.sub(r'(?i)(st|nd|rd|th)\b', '', sale_date_str).strip()
                            # Find the month name in the string
                            month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', sale_date_str)
                            if month_match:
                                sale_month_name = month_match.group(1)
                                try:
                                    sale_month = datetime.strptime(sale_month_name, '%B').month
                                except ValueError:
                                    print(f"Invalid month name: {sale_month_name}")
                                    continue

                            if sale_month == 1 and post_date.month == 12:
                                sale_year = post_year + 1
                            else:
                                sale_year = post_year
                            sale_date_str = sale_date_str.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                            sale_date_obj = parse_date(sale_date_str, sale_year)
                            sale_date = sale_date_obj.strftime('%d-%m-%Y')
                    else:
                        sale_date = sale_date_str
                    date_found = True
                    break
            
            # If no date was found or it's a current sale, use post date
            if (not date_found or is_current_sale or sale_date == 'N/A') and post_date_str != 'N/A':
                sale_date = post_date_str
            
            # Extract sale discount
            sale_discount_match = re.search(r'\b\d+% off\b', post['caption'])
            if sale_discount_match:
                sale_discount = sale_discount_match.group().replace(' off', '')
            
            # Check for sitewide sale
            is_sitewide = any(re.search(pattern, post['caption']) for pattern in sitewide_patterns)
        else:
            is_sitewide = False
        
        # Initialize event
        event = 'N/A'
        
        # Check for specific events only if it's a sale post
        if is_sale_post:
            # First check for EOFY Sale based on date
            if post_date_str != 'N/A':
                post_date = datetime.strptime(post_date_str, '%d-%m-%Y')
                if (post_date.month == 6 and post_date.day >= 25) or (post_date.month == 7 and post_date.day <= 7):
                    event = "EOFY Sale"
            
            # Only check other events if it's not already marked as EOFY Sale
            if event == 'N/A':
                for pattern in event_patterns:
                    event_match = re.search(pattern, post['caption'].lower())
                    if event_match:
                        event_name = event_match.group().title()
                        # Check if the event is plausible based on the post date
                        if event_name == "Christmas" and (post_date.month != 12 or post_date.day < 11 or post_date.day > 25):
                            continue
                        if event_name == "Black Friday" and (
                            (post_date.month != 11 and post_date.month != 12) or 
                            (post_date.month == 11 and post_date.day < 17) or  # Week before Black Friday
                            (post_date.month == 12 and post_date.day > 7)  # First week of December
                        ):
                            continue
                        # Add more conditions for other events if necessary
                        event = event_name
                        break
        
        sale_info = {
            'caption': post['caption'],
            'post_date': post_date_str,
            'sale_date': sale_date,
            'sale_discount': sale_discount,
            'sitewide': 1 if is_sitewide else 0,
            'y': 1 if is_sale_post else 0,
            'brand': post['brand'],
            'likesCount': post.get('likesCount', '0'),
            'commentsCount': post.get('commentsCount', '0'),
            'url': post.get('url', 'N/A'),
            'event': event  # Add event to the sale_info dictionary
        }
        result.append(sale_info)
    
    return result

# Read posts from a CSV file
def read_posts_from_csv(file_path):
    # Extract brand name from file path
    brand_name = re.search(r'([^/\\]+)Dataset', file_path, re.IGNORECASE)
    brand_name = brand_name.group(1).lower() if brand_name else 'unknown'
    
    # Replace hyphens with spaces in brand name
    brand_name = brand_name.replace('-', ' ')
    
    posts = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            posts.append({
                'id': row.get('id', 'N/A'),
                'caption': row['caption'],
                'url': row.get('url', 'N/A'),
                'post_date': row.get('timestamp', 'N/A'),
                'likesCount': row.get('likesCount', '0'),
                'commentsCount': row.get('commentsCount', '0'),
                'brand': brand_name
            })
    return posts

def parse_date(date_str, year=None):
    formats = ['%B %d %Y', '%d %B %Y', '%d-%m-%Y', '%m-%d-%Y']
    
    # Normalize the month name first
    date_str = normalize_month_name(date_str)
    
    # Clean up the date string to handle cases with duplicate day numbers
    # Extract month name
    month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', date_str)
    if month_match:
        month = month_match.group(1)
        # Extract the first number that appears
        day_match = re.search(r'\b(\d{1,2})\b', date_str)
        if day_match:
            day = day_match.group(1)
            # Reconstruct the date string
            date_str = f"{day} {month}"
    
    if year:
        date_str = f"{date_str} {year}"
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date string '{date_str}' does not match any expected format")

def normalize_month_name(date_str):
    month_mappings = {
        'jan': 'January', 'feb': 'February', 'mar': 'March',
        'apr': 'April', 'may': 'May', 'jun': 'June',
        'jul': 'July', 'aug': 'August', 'sep': 'September',
        'oct': 'October', 'nov': 'November', 'dec': 'December'
    }
    
    words = date_str.split()
    for i, word in enumerate(words):
        word_lower = word.lower()
        for short_month, full_month in month_mappings.items():
            if word_lower.startswith(short_month):
                words[i] = full_month
                break
    
    return ' '.join(words)

# Example usage:
file_path = './white-fox/white-foxDataset.csv'
instagram_posts = read_posts_from_csv(file_path)
sales_info = filter_sales_posts(instagram_posts)

# Remove ID field from each dictionary in sales_info
for post in sales_info:
    if 'id' in post:
        del post['id']

# After collecting all sales_info
# Convert dates for proper sorting
def convert_date(date_str):
    if date_str == 'N/A':
        return datetime.min
    try:
        return datetime.strptime(date_str, '%d-%m-%Y')
    except ValueError:
        return datetime.min

# Sort the data by post_date (newest first)
sales_info = sorted(
    sales_info,
    key=lambda x: convert_date(x['post_date']),
    reverse=True
)

# Save to CSV file
input_directory = os.path.dirname(file_path)
capitalized_brand = ''.join(word.capitalize() for word in sales_info[0]["brand"].split())
output_file = os.path.join(input_directory, f'prepped{capitalized_brand}Dataset.csv')
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'brand', 'caption', 'post_date', 'y', 'sale_date', 
        'sale_discount', 'sitewide', 'likesCount', 'commentsCount',
        'url', 'event'  # Include event in the CSV header
    ])
    writer.writeheader()
    writer.writerows(sales_info)

print(f"Data has been saved to {output_file}")