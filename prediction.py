import re
from datetime import datetime, timedelta
from collections import Counter
from sortPosts import filter_sales_posts, read_posts_from_csv

def predict_next_sale(file_path):
    # Read posts and filter sales information
    instagram_posts = read_posts_from_csv(file_path)
    sales_info = filter_sales_posts(instagram_posts)
    
    # Extract sale dates and discounts from sales_info
    sale_dates = []
    sale_discounts = []
    for sale in sales_info:
        if sale['sale_date'] != 'N/A':
            try:
                sale_date = datetime.strptime(sale['sale_date'], '%d %B %Y')
                sale_dates.append(sale_date)
            except ValueError as e:
                print(f"Error parsing date: {sale['sale_date']} - {e}")
                continue
        if sale['sale_discount'] != 'N/A':
            discount_match = re.search(r'\d+', sale['sale_discount'])
            if discount_match:
                sale_discounts.append(int(discount_match.group()))
    
    if not sale_dates or not sale_discounts:
        print("No valid sale dates or discounts found.")
        return {
            'next_sale_date': 'N/A',
            'predicted_discount': 'N/A',
            'probability': 0.0
        }
    
    # Predict the next sale date
    sale_dates.sort()
    intervals = [(sale_dates[i] - sale_dates[i-1]).days for i in range(1, len(sale_dates))]
    avg_interval = sum(intervals) / len(intervals) if intervals else 30  # Default to 30 days if no intervals
    last_sale_date = sale_dates[-1]
    next_sale_date = last_sale_date + timedelta(days=avg_interval)
    
    # Predict the most likely discount
    discount_counter = Counter(sale_discounts)
    most_common_discount = discount_counter.most_common(1)[0][0]
    
    # Calculate the probability of the sale happening
    probability = len(sale_dates) / ((datetime.now() - sale_dates[0]).days / avg_interval)
    
    return {
        'next_sale_date': next_sale_date.strftime('%d/%m/%Y'),
        'predicted_discount': f"{most_common_discount}%",
        'probability': min(probability, 1.0)  # Probability should not exceed 1
    }

# Example usage:
file_path = 'Instagram Scraper Dataset Nov 26 2024.csv'
predicted_sale = predict_next_sale(file_path)
print(predicted_sale)

