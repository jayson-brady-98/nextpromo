import pandas as pd
from prophet import Prophet
import os
from datetime import datetime

# Read the CSV file
data = pd.read_csv('gymshark_NEW/p_gymshark.csv')

# Create main dataframe for Prophet
df = pd.DataFrame({
    'ds': pd.to_datetime(data['snapshot'].astype(str), format='%Y%m%d%H%M%S'),
    'y': data['y'].astype(int)
})

# Process events data - only get rows where event is not empty for holidays
events = data[data['event'].notna() & (data['event'] != '')].copy()
print(f"Number of events found: {len(events)}")
print("Event types found:", events['event'].unique())

# Define event windows
event_windows = {
    'Black Friday': {
        'lower_window': -14,  # Two weeks before
        'upper_window': 7,    # One week after
        'prior_scale': 10     # Strong effect
    },
    'Summer/Winter Sale': {
        'lower_window': -7,
        'upper_window': 14,
        'prior_scale': 8
    },
    'Singles Day': {
        'lower_window': -3,
        'upper_window': 2,
        'prior_scale': 5
    },
    'default': {
        'lower_window': -5,
        'upper_window': 5,
        'prior_scale': 5
    }
}

# Create holidays DataFrame
holidays_data = []
for _, event_row in events.iterrows():
    event_type = event_row['event']
    event_date = pd.to_datetime(event_row['snapshot'], format='%Y%m%d%H%M%S')
    
    windows = event_windows.get(event_type, event_windows['default'])
    
    holidays_data.append({
        'holiday': event_type,
        'ds': event_date,
        'lower_window': windows['lower_window'],
        'upper_window': windows['upper_window'],
        'prior_scale': windows['prior_scale']
    })

# Add future events
future_holidays = []
for year in range(2025, 2027):
    future_holidays.extend([
        {
            'holiday': 'Black Friday',
            'ds': pd.Timestamp(f'{year}-11-24'),
            'lower_window': event_windows['Black Friday']['lower_window'],
            'upper_window': event_windows['Black Friday']['upper_window'],
            'prior_scale': event_windows['Black Friday']['prior_scale']
        },
        {
            'holiday': 'Summer/Winter Sale',
            'ds': pd.Timestamp(f'{year}-06-30'),
            'lower_window': event_windows['Summer/Winter Sale']['lower_window'],
            'upper_window': event_windows['Summer/Winter Sale']['upper_window'],
            'prior_scale': event_windows['Summer/Winter Sale']['prior_scale']
        },
        {
            'holiday': 'Singles Day',
            'ds': pd.Timestamp(f'{year}-11-11'),
            'lower_window': event_windows['Singles Day']['lower_window'],
            'upper_window': event_windows['Singles Day']['upper_window'],
            'prior_scale': event_windows['Singles Day']['prior_scale']
        }
    ])

# Combine historical and future holidays
holidays = pd.concat([
    pd.DataFrame(holidays_data),
    pd.DataFrame(future_holidays)
]).reset_index(drop=True)

# Initialize and configure model
model = Prophet(
    holidays=holidays,
    yearly_seasonality=20,
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_prior_scale=15,
    holidays_prior_scale=10,
    changepoint_prior_scale=0.08
)

# Add regressors for additional features
if 'sitewide' in data.columns:
    df['sitewide'] = data['sitewide']
    model.add_regressor('sitewide')

# Fit model
model.fit(df)

# Create future dataframe for 365 days
future = model.make_future_dataframe(periods=365)

# Add regressor values to future dataframe if needed
if 'sitewide' in df.columns:
    future['sitewide'] = df['sitewide'].mean()  # Use mean as default

# Make predictions
forecast = model.predict(future)

# Save predictions
output_file = 'gymshark_NEW/gymshark_predictions.csv'
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(output_file, index=False)
print(f"Predictions saved to {output_file}")
