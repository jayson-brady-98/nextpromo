import pandas as pd
from prophet import Prophet
import os
from datetime import datetime

# Read the CSV file with keep_default_na=False to prevent empty strings becoming NaN
data = pd.read_csv('vpa/preppedVpaDataset.csv', keep_default_na=False)

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
    'Black Friday': {
        'lower_window': -21,  
        'upper_window': 5,    
        'prior_scale': 8      # Keep this consistent
    },
    'Cyber Monday': {
        'lower_window': -3,   
        'upper_window': 2,
        'prior_scale': 8
    },
    'Christmas': {
        'lower_window': -14,
        'upper_window': 2,
        'prior_scale': 8
    },
    'default': {
        'lower_window': -7,
        'upper_window': 2,
        'prior_scale': 5
    }
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

# Add future holiday dates with CONSISTENT prior_scale values
future_holidays = []
for year in range(2024, 2026):  # Adjust range as needed
    future_holidays.extend([
        {
            'holiday': 'Black Friday',
            'ds': pd.Timestamp(f'{year}-11-24'),  # Approximate date
            'lower_window': event_windows['Black Friday']['lower_window'],
            'upper_window': event_windows['Black Friday']['upper_window'],
            'prior_scale': event_windows['Black Friday']['prior_scale']  # Use same value
        },
        {
            'holiday': 'Christmas',
            'ds': pd.Timestamp(f'{year}-12-25'),
            'lower_window': event_windows['Christmas']['lower_window'],
            'upper_window': event_windows['Christmas']['upper_window'],
            'prior_scale': event_windows['Christmas']['prior_scale']
        },
        {
            'holiday': 'Cyber Monday',
            'ds': pd.Timestamp(f'{year}-11-27'),  # Approximate date
            'lower_window': event_windows['Cyber Monday']['lower_window'],
            'upper_window': event_windows['Cyber Monday']['upper_window'],
            'prior_scale': event_windows['Cyber Monday']['prior_scale']
        },
        {
            'holiday': 'EOFY Sale',
            'ds': pd.Timestamp(f'{year}-06-30'),
            'lower_window': event_windows['default']['lower_window'],
            'upper_window': event_windows['default']['upper_window'],
            'prior_scale': event_windows['default']['prior_scale']
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
    yearly_seasonality=25,    
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_prior_scale=20,  # Moderate seasonality emphasis
    holidays_prior_scale=8,      # Let the holiday patterns speak for themselves
    changepoint_prior_scale=0.05 # Help detect natural changes in patterns
)

# Fit the model
model.fit(df)

# Create future dataframe
future = model.make_future_dataframe(periods=365)

# Make predictions
forecast = model.predict(future)

# Save predictions
input_file = 'vpa/preppedVpaDataset.csv'
input_directory = os.path.dirname(input_file)
brand_name = input_file.split('prepped')[1].split('Dataset')[0]
output_file = os.path.join(input_directory, f'{brand_name.lower()}Prediction.csv')

forecast[['ds', 'yhat']].to_csv(output_file, index=False)
print(f"Predictions saved to {output_file}")
