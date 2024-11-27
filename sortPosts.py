import csv
import re
import json

# Function to filter Instagram posts for sales information
def filter_sales_posts(posts):
    # Expanded keywords related to sales
    sale_keywords = [
        'sale', 'discount', '% off', 'clearance',
        'deal', 'code', 'promotion', 'promo', 
        'offer'
    ]
    
    # Filter posts that mention sales
    sales_posts = [
        post for post in posts 
        if any(re.search(keyword, post['caption'].lower()) for keyword in sale_keywords)
    ]
    
    # Extract sale details from filtered posts
    result = []
    for post in sales_posts:
        sale_info = {
            'id': post.get('id', 'N/A'),
            'caption': post['caption'],
            'post_date': post.get('post_date', 'N/A'),
            'sale_date': re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', post['caption']).group() if re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', post['caption']) else 'N/A',
            'sale_discount': re.search(r'\b\d+% off\b', post['caption']).group() if re.search(r'\b\d+% off\b', post['caption']) else 'N/A'
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

# Example usage:
file_path = 'Instagram Scraper Dataset Nov 26 2024.csv'
instagram_posts = read_posts_from_csv(file_path)
sales_info = filter_sales_posts(instagram_posts)

# Convert to JSON string
sales_info_json = json.dumps(sales_info, indent=4)
print(sales_info_json)
