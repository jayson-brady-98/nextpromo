import csv
import re
from datetime import datetime

# Function to filter Instagram posts for sales information
def filter_sales_posts(posts):
    # More specific sale-related patterns using regex
    sale_patterns = [
        r'\b(?:flash |huge |big )?sale\b',  # "sale" with optional prefixes
        r'\b\d+%\s*off\b',  # percentage discounts
        r'\bclearance\b',
        r'\bpromo(?:tion)?\s+code[:\s]\s*[A-Z0-9]+\b',  # promo codes with actual code
        r'\bspecial\s+offer\b',
        r'\bdiscount\s+(?:code|price)',
        r'\bdeals?\s+(?:of|this|today)\b'  # deals with qualifying words
    ]
    
    date_patterns = [
        r'\b(?:\d{1,2}(?:st|nd|rd|th|ST|ND|RD|TH)? )?(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(?:st|nd|rd|th|ST|ND|RD|TH)?\b',
        r'\b\d{1,2}(?:st|nd|rd|th|ST|ND|RD|TH)? (January|February|March|April|May|June|July|August|September|October|November|December)\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
    ]
    
    # Add sitewide patterns
    sitewide_patterns = [
        r'(?i)\bsitewide\b',
        r'(?i)\d+%\s+off\s+everything\b'
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
            'url': post.get('url', 'N/A')
        }
        result.append(sale_info)
    
    return result

# Read posts from a CSV file
def read_posts_from_csv(file_path):
    # Extract brand name from file path
    brand_name = re.search(r'([^/\\]+)Dataset', file_path, re.IGNORECASE)
    brand_name = brand_name.group(1).lower() if brand_name else 'unknown'
    
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
    if year:
        date_str = f"{date_str} {year}"
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date string '{date_str}' does not match any expected format")

# Example usage:
file_path = 'gymsharkDataset.csv'
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
output_file = f'prepped{sales_info[0]["brand"].capitalize()}Dataset.csv'
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'brand', 'caption', 'post_date', 'y', 'sale_date', 
        'sale_discount', 'sitewide', 'likesCount', 'commentsCount',
        'url'
    ])
    writer.writeheader()
    writer.writerows(sales_info)

print(f"Data has been saved to {output_file}")