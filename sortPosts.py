import csv
import re
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
    
    # Extract sale details from posts
    result = []
    for post in posts:
        # Check if the post mentions sales
        is_sale_post = any(re.search(keyword, post['caption'].lower()) for keyword in sale_keywords)
        
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
            # Find the sale date in the caption
            for pattern in date_patterns:
                date_match = re.search(pattern, post['caption'])
                if date_match:
                    sale_date_str = date_match.group()
                    # If the date is in "Month Day" or "Day Month" format, append the year
                    if re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', sale_date_str):
                        if post_year:
                            # Determine the correct year
                            sale_month_name = sale_date_str.split()[1]  # Assuming the month is the second word
                            try:
                                sale_month = datetime.strptime(sale_month_name, '%B').month
                            except ValueError:
                                # Handle the error or log it
                                print(f"Invalid month name: {sale_month_name}")
                                sale_month = None  # or some default value
                            if sale_month == 1 and post_date.month == 12:
                                sale_year = post_year + 1
                            else:
                                sale_year = post_year
                            sale_date_str = sale_date_str.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                            sale_date_obj = parse_date(sale_date_str, sale_year)
                            sale_date = sale_date_obj.strftime('%d-%m-%Y')
                    else:
                        sale_date = sale_date_str
                    break
            
            # Extract sale discount
            sale_discount_match = re.search(r'\b\d+% off\b', post['caption'])
            if sale_discount_match:
                sale_discount = sale_discount_match.group().replace(' off', '')
        
        sale_info = {
            'caption': post['caption'],
            'post_date': post_date_str,
            'sale_date': sale_date,
            'sale_discount': sale_discount,
            'is_sale_post': is_sale_post,
            'brand': 'gymshark'
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
                'post_date': row.get('timestamp', 'N/A')  # Use 'timestamp' column for post_date
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
file_path = 'Instagram Scraper Dataset Nov 26 2024.csv'
instagram_posts = read_posts_from_csv(file_path)
sales_info = filter_sales_posts(instagram_posts)

# Remove ID field from each dictionary in sales_info
for post in sales_info:
    if 'id' in post:
        del post['id']

# Save to CSV file
output_file = 'gymshark_sales_data.csv'
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'caption', 'post_date', 'sale_date', 
        'sale_discount', 'is_sale_post', 'brand'
    ])
    writer.writeheader()
    writer.writerows(sales_info)

print(f"Data has been saved to {output_file}")