import pandas as pd
from prophet import Prophet
import os

# Read the CSV file
data = pd.read_csv('white-fox/preppedWhiteFoxDataset.csv')

# Create the main dataframe for Prophet
df = pd.DataFrame({
    'ds': pd.to_datetime(data['post_date'], format='%d-%m-%Y'),
    'y': data['y'].astype(int),
    'likes': data['likesCount'],
    'comments': data['commentsCount']
})

# Create separate holiday DataFrames for different types of events
# Filter out empty events and sale_dates
sales_events = data[
    (data['event'] != '') & 
    (data['sale_date'] != '') &
    (data['sale_date'].notna())  # Additional check for NaN values
].copy()

# Convert sale_date to datetime
sales_events['sale_date'] = pd.to_datetime(sales_events['sale_date'], format='%d-%m-%Y')

# Define different windows for different types of events
event_windows = {
    'Black Friday': {'lower_window': -14, 'upper_window': 3},
    'EOFY Sale': {'lower_window': -10, 'upper_window': 2},
    'Christmas': {'lower_window': -14, 'upper_window': 2},
    'Cyber Monday': {'lower_window': -7, 'upper_window': 1},
    'default': {'lower_window': -7, 'upper_window': 2}
}

# Create holidays DataFrame with different windows for different events
holidays_data = []
for _, event_row in sales_events.iterrows():
    try:
        event_type = event_row['event']
        sale_date = pd.to_datetime(event_row['sale_date'], format='%d-%m-%Y')
        
        # Skip if either value is empty or NaN
        if pd.isna(event_type) or pd.isna(sale_date) or event_type == '' or sale_date == '':
            continue
            
        windows = event_windows.get(event_type, event_windows['default'])
        
        holidays_data.append({
            'holiday': event_type,
            'ds': sale_date,
            'lower_window': windows['lower_window'],
            'upper_window': windows['upper_window']
        })
    except (ValueError, TypeError) as e:
        print(f"Skipping invalid event: {e}")
        continue

holidays = pd.DataFrame(holidays_data)

# Debug print
print("Holidays DataFrame shape:", holidays.shape)
print("Holidays columns with NaN:", holidays.isna().sum())

if len(holidays) == 0:
    print("No valid holiday events found")
    holidays = None
elif holidays.isna().any().any():
    print("Removing rows with NaN values")
    holidays = holidays.dropna()

# Add regressors and events to the model
model = Prophet(holidays=holidays if holidays is not None and len(holidays) > 0 else None)
model.add_regressor('likes')
model.add_regressor('comments')

# Fit the model
model.fit(df)

# For future predictions, we need to include the regressor values
future = model.make_future_dataframe(periods=365)

# Use more sophisticated approach for future regressor values
window_size = 30  # 30-day rolling average
rolling_likes = df['likes'].rolling(window=window_size).mean().iloc[-1]
rolling_comments = df['comments'].rolling(window=window_size).mean().iloc[-1]

future['likes'] = rolling_likes
future['comments'] = rolling_comments

# Make predictions
forecast = model.predict(future)

# Extract brand name from input filename and save predictions
input_file = 'white-fox/preppedWhiteFoxDataset.csv'
input_directory = os.path.dirname(input_file)
brand_name = input_file.split('prepped')[1].split('Dataset')[0]
output_file = os.path.join(input_directory, f'{brand_name.lower()}Prediction.csv')

# Save predictions to a CSV using the extracted brand name in camelCase
forecast[['ds', 'yhat']].to_csv(output_file, index=False)
print(f"Predictions saved to {output_file}")
