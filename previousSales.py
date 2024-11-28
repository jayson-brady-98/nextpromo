import re
from sortPosts import filter_sales_posts, read_posts_from_csv
from datetime import datetime

def extract_sale_event(caption):
    # Common sale event names
    event_keywords = {
        'black friday': 'Black Friday',
        'cyber monday': 'Cyber Monday',
        'boxing day': 'Boxing Day',
        'birthday': 'Birthday Sale',
        'summer sale': 'Summer Sale',
        'winter sale': 'Winter Sale',
        'spring sale': 'Spring Sale',
        'fall sale': 'Fall Sale',
        'christmas': 'Christmas Sale',
        'end of season sale': 'End of Season Sale',
        'clearance': 'Clearance Sale'
    }
    
    caption_lower = caption.lower()
    
    # Check for known event names first
    for keyword, event_name in event_keywords.items():
        if keyword in caption_lower:
            return event_name
            
    # Default to "Generic Sale" if no specific event or keyword found
    return "Generic Sale"

def get_previous_sales():
    # Read and filter sales posts
    file_path = 'Instagram Scraper Dataset Nov 26 2024.csv'
    instagram_posts = read_posts_from_csv(file_path)
    sales_info = filter_sales_posts(instagram_posts)
    
    # Filter valid sales with dates and sort by date
    valid_sales = [
        sale for sale in sales_info 
        if sale['sale_date'] != 'N/A' and sale['is_sale_post']
    ]
    
    # Convert dates to datetime objects for sorting
    for sale in valid_sales:
        sale['date_obj'] = datetime.strptime(sale['sale_date'], '%d-%m-%Y')
    
    # Sort by date in descending order
    valid_sales.sort(key=lambda x: x['date_obj'], reverse=True)
    
    # Get the 6 most recent sales
    recent_sales = valid_sales[:6]
    
    # Format and print the results
    print("\nPrevious 6 Gymshark Sales:")
    print("-" * 50)
    for sale in recent_sales:
        event = extract_sale_event(sale['caption'])
        discount = sale['sale_discount'] if sale['sale_discount'] != 'N/A' else 'Discount not specified'
        date = sale['sale_date']
        print(f"Event: {event}")
        print(f"Discount: {discount}")
        print(f"Date: {date}")
        print("-" * 50)

if __name__ == "__main__":
    get_previous_sales()
    def get_unique_previous_sales():
        # Read and filter sales posts
        file_path = 'Instagram Scraper Dataset Nov 26 2024.csv'
        instagram_posts = read_posts_from_csv(file_path)
        sales_info = filter_sales_posts(instagram_posts)
        
        # Filter valid sales with dates
        valid_sales = [
            sale for sale in sales_info 
            if sale['sale_date'] != 'N/A' and sale['is_sale_post']
        ]
        
        # Convert dates to datetime objects and create unique sales dict
        unique_sales = {}
        for sale in valid_sales:
            date_obj = datetime.strptime(sale['sale_date'], '%d-%m-%Y')
            # Use date as key to avoid duplicates
            # If multiple posts exist for same date, keep the one with most info
            if date_obj not in unique_sales or (
                sale['sale_discount'] != 'N/A' and unique_sales[date_obj]['sale_discount'] == 'N/A'
            ):
                unique_sales[date_obj] = sale
        
        # Sort dates in descending order
        sorted_dates = sorted(unique_sales.keys(), reverse=True)
        
        # Get the 6 most recent unique sales
        recent_sales = [unique_sales[date] for date in sorted_dates[:6]]
        
        # Format and print the results
        print("\nPrevious 6 Unique Gymshark Sales:")
        print("-" * 50)
        for sale in recent_sales:
            event = extract_sale_event(sale['caption'])
            discount = sale['sale_discount'] if sale['sale_discount'] != 'N/A' else 'Discount not specified'
            date = sale['sale_date']
            print(f"Event: {event}")
            print(f"Discount: {discount}")
            print(f"Date: {date}")
            print("-" * 50)

    if __name__ == "__main__":
        get_unique_previous_sales()
