import pandas as pd
import numpy as np
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA
from datetime import timedelta
from sortPosts import filter_sales_posts, read_posts_from_csv
from statsmodels.tsa.seasonal import seasonal_decompose

def predict_next_sale_date(sales_info):
    # Extract valid sale dates
    valid_sale_dates = [
        datetime.strptime(sale['sale_date'], '%d-%m-%Y')
        for sale in sales_info
        if sale['sale_date'] != 'N/A'
    ]
    
    if not valid_sale_dates:
        return "No valid sale dates available for prediction."
    
    # Sort dates and calculate the average interval
    valid_sale_dates.sort()
    intervals = [
        (valid_sale_dates[i] - valid_sale_dates[i - 1]).days
        for i in range(1, len(valid_sale_dates))
    ]
    
    if not intervals:
        return "Not enough data to predict the next sale date."
    
    average_interval = sum(intervals) / len(intervals)
    
    # Predict the next sale date
    last_sale_date = valid_sale_dates[-1]
    next_sale_date = last_sale_date + pd.Timedelta(days=int(average_interval))
    
    # Check for Black Friday
    current_year = datetime.now().year
    black_friday = calculate_black_friday(current_year)
    if black_friday > last_sale_date and black_friday < next_sale_date:
        next_sale_date = black_friday
    
    # Check if the predicted sale date is today
    today = datetime.now().date()
    if next_sale_date.date() == today:
        return "Gymshark is currently running a sale."
    
    return next_sale_date.strftime('%d-%m-%Y')

def calculate_black_friday(year):
    # Black Friday is the day after the fourth Thursday in November
    november_first = datetime(year, 11, 1)
    first_thursday = november_first + timedelta(days=(3 - november_first.weekday() + 7) % 7)
    black_friday = first_thursday + timedelta(weeks=3, days=1)
    return black_friday

def main():
    # Read posts from CSV and filter for sales information
    file_path = 'Instagram Scraper Dataset Nov 26 2024.csv'
    instagram_posts = read_posts_from_csv(file_path)
    sales_info = filter_sales_posts(instagram_posts)
    
    # Predict the next sale date
    next_sale = predict_next_sale_date(sales_info)
    print(f"Predicted next sale date: {next_sale}")

if __name__ == "__main__":
    main() 