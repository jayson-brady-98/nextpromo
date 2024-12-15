import pandas as pd
from prophet import Prophet
import os
from datetime import datetime

# Read the CSV file with keep_default_na=False to prevent empty strings becoming NaN
data = pd.read_csv('white-fox/preppedWhiteFoxDataset.csv', keep_default_na=False)

# Create the main dataframe for Prophet
df = pd.DataFrame({
    'ds': pd.to_datetime(data['post_date'], format='%d-%m-%Y'),
    'y': data['y'].astype(int),
    'likes': data['likesCount'],
    'comments': data['commentsCount']
})

# Filter and process historical events - only looking for non-empty events
sales_events = data[
    (data['event'] != '') & 
    (data['sale_date'] != '')
].copy()

print(f"Number of historical events found: {len(sales_events)}")
print("Event types found:", sales_events['event'].unique())

# Define different windows for different types of events with stronger effects
event_windows = {
    'Black Friday': {'lower_window': -14, 'upper_window': 3, 'prior_scale': 10},
    'EOFY Sale': {'lower_window': -10, 'upper_window': 2, 'prior_scale': 8},
    'Christmas': {'lower_window': -14, 'upper_window': 2, 'prior_scale': 8},
    'Cyber Monday': {'lower_window': -7, 'upper_window': 1, 'prior_scale': 8},
    'default': {'lower_window': -7, 'upper_window': 2, 'prior_scale': 5}
}

# Create holidays DataFrame from historical events
holidays_data = []
for _, event_row in sales_events.iterrows():
    try:
        event_type = event_row['event']
        sale_date = pd.to_datetime(event_row['sale_date'], format='%d-%m-%Y')
        
        # Skip empty strings
        if event_type == '' or not sale_date:
            continue
            
        windows = event_windows.get(event_type, event_windows['default'])
        
        holidays_data.append({
            'holiday': event_type,
            'ds': sale_date,
            'lower_window': windows['lower_window'],
            'upper_window': windows['upper_window'],
            'prior_scale': windows['prior_scale']
        })
    except ValueError as e:
        print(f"Skipping invalid event: {e}")
        continue

# Add future holiday dates
future_holidays = []
for year in range(2024, 2026):  # Adjust range as needed
    future_holidays.extend([
        {
            'holiday': 'Black Friday',
            'ds': pd.Timestamp(f'{year}-11-24'),  # Approximate date
            'lower_window': -14,
            'upper_window': 3,
            'prior_scale': 10
        },
        {
            'holiday': 'Christmas',
            'ds': pd.Timestamp(f'{year}-12-25'),
            'lower_window': -14,
            'upper_window': 2,
            'prior_scale': 8
        },
        {
            'holiday': 'Cyber Monday',
            'ds': pd.Timestamp(f'{year}-11-27'),  # Approximate date
            'lower_window': -7,
            'upper_window': 1,
            'prior_scale': 8
        },
        {
            'holiday': 'EOFY Sale',
            'ds': pd.Timestamp(f'{year}-06-30'),
            'lower_window': -10,
            'upper_window': 2,
            'prior_scale': 8
        }
    ])

# Combine historical and future holidays
holidays = pd.concat([
    pd.DataFrame(holidays_data),
    pd.DataFrame(future_holidays)
]).reset_index(drop=True)

# Initialize and configure the model with stronger seasonality
model = Prophet(
    holidays=holidays,
    yearly_seasonality=30,  # Increased from 20
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_prior_scale=30,  # Increased from 20
    holidays_prior_scale=15  # Increased from 10
)

model.add_regressor('likes')
model.add_regressor('comments')

# Fit the model
model.fit(df)

# Create future dataframe
future = model.make_future_dataframe(periods=365)

# Add regressor values for future predictions
window_size = 30
rolling_likes = df['likes'].rolling(window=window_size).mean().iloc[-1]
rolling_comments = df['comments'].rolling(window=window_size).mean().iloc[-1]

future['likes'] = rolling_likes
future['comments'] = rolling_comments

# Make predictions
forecast = model.predict(future)

# Save predictions
input_file = 'white-fox/preppedWhiteFoxDataset.csv'
input_directory = os.path.dirname(input_file)
brand_name = input_file.split('prepped')[1].split('Dataset')[0]
output_file = os.path.join(input_directory, f'{brand_name.lower()}Prediction.csv')

forecast[['ds', 'yhat']].to_csv(output_file, index=False)
print(f"Predictions saved to {output_file}")
