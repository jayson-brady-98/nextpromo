import pandas as pd
import numpy as np
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA
from datetime import timedelta
from sortPosts import filter_sales_posts, read_posts_from_csv

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
    
    return next_sale_date.strftime('%d-%m-%Y')

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
