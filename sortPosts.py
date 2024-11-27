import csv
import re
import json
from datetime import datetime

# Function to filter Instagram posts for sales information
def filter_sales_posts(posts):
    # Expanded keywords related to sales
    sale_keywords = [
        'sale', 'discount', '% off', 'clearance',
        'deal', 'code', 'promotion', 'promo', 
        'offer'
    ]
    
    # Regex patterns for date extraction
    date_patterns = [
        r'\b(?:\d{1,2}(?:st|nd|rd|th)? )?(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(?:st|nd|rd|th)?\b',  # Month name dates with day
        r'\b\d{1,2}(?:st|nd|rd|th)? (January|February|March|April|May|June|July|August|September|October|November|December)\b',  # Day before month
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'  # Numeric dates
    ]
    
    # Filter posts that mention sales
    sales_posts = [
        post for post in posts 
        if any(re.search(keyword, post['caption'].lower()) for keyword in sale_keywords)
    ]
    
    # Extract sale details from filtered posts
    result = []
    for post in sales_posts:
        # Extract the year from the post_date
        post_date_str = post.get('post_date', 'N/A')
        post_year = None
        if post_date_str != 'N/A':
            try:
                post_date = datetime.strptime(post_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                post_year = post_date.year
                post_date_str = post_date.strftime('%Y-%m-%d')  # Format post_date as ISO 8601
            except ValueError:
                post_year = None
        
        # Find the sale date in the caption
        sale_date = 'N/A'
        for pattern in date_patterns:
            date_match = re.search(pattern, post['caption'])
            if date_match:
                sale_date_str = date_match.group()
                # Remove ordinal suffixes from the day
                sale_date_str = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', sale_date_str)
                # If the date is in "Month Day" or "Day Month" format, append the year
                month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', sale_date_str)
                if month_match:
                    if post_year:
                        # Determine the correct year
                        sale_month = datetime.strptime(month_match.group(), '%B').month
                        if sale_month == 1 and post_date.month == 12:
                            sale_year = post_year + 1
                        else:
                            sale_year = post_year
                        # Parse and format the sale date as ISO 8601
                        try:
                            sale_date = datetime.strptime(f"{sale_date_str} {sale_year}", '%d %B %Y').strftime('%Y-%m-%d')
                        except ValueError:
                            sale_date = 'N/A'
                else:
                    sale_date = sale_date_str
                break
        
        sale_info = {
            'id': post.get('id', 'N/A'),
            'caption': post['caption'],
            'post_date': post_date_str,
            'sale_date': sale_date,
            'sale_discount': re.search(r'\b\d+% off\b', post['caption']).group() if re.search(r'\b\d+% off\b', post['caption']) else 'N/A',
            'url': post.get('url', 'N/A'),  # Include the URL from the dataset
            'company_name': 'Gymshark'  # Include the company name
        }
        result.append(sale_info)
    
    return result

# Read posts from a CSV file
def read_posts_from_csv(file_path):
    posts = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            posts.append({
                'id': row.get('id', 'N/A'),  # Assuming there's an 'id' column
                'caption': row['caption'],
                'permalink': row.get('permalink', 'N/A'),  # Assuming there's a 'permalink' column
                'post_date': row.get('timestamp', 'N/A'),  # Use 'timestamp' column for post_date
                'url': row.get('url', 'N/A')  # Assuming there's a 'url' column
            })
    return posts

# Example usage:
file_path = 'Instagram Scraper Dataset Nov 26 2024.csv'
instagram_posts = read_posts_from_csv(file_path)
sales_info = filter_sales_posts(instagram_posts)

# Convert to JSON string
sales_info_json = json.dumps(sales_info, indent=4)
print(sales_info_json)
