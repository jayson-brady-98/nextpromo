import pandas as pd
from prophet import Prophet
import os
from datetime import datetime
from dataCleaning import DataPaths

def train_model(brand: str):
    # Initialize paths
    paths = DataPaths(brand)
    
    # Read the CSV file using the paths
    data = pd.read_csv(paths.prophet_data)
    
    # Create main dataframe for Prophet
    df = pd.DataFrame({
        'ds': pd.to_datetime(data['snapshot'].astype(str), format='%Y%m%d%H%M%S'),
        'y': data['y'].astype(int)
    })
    
    # Initialize and configure model with adjusted seasonality
    model = Prophet(
        changepoint_prior_scale=0.0005,  # Adjusted for noise
        yearly_seasonality=30,  # Increased Fourier terms for yearly seasonality
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_prior_scale=15
    )
    
    # Add custom seasonality if needed
    model.add_seasonality(name='quarterly', period=91.25, fourier_order=8)
    
    # Fit model
    model.fit(df)
    
    # Define retail events with their annual dates (month, day)
    retail_event_dates = {
        'black_friday': [(11, 24)],  # Needs special handling for "last Friday of November"
        'cyber_monday': [(11, 27)],  # First Monday after Black Friday
        'boxing_day': [(12, 26)],
        'singles_day': [(11, 11)],
        'international_womens_day': [(3, 8)],
        'eofy': [(6, 30)],  # End of Financial Year
        'labor_day': [(9, 1)],  # Needs special handling for "first Monday in September"
        'summer_winter_sale': [
            (12, 26), (12, 27), (12, 28), (12, 29), (12, 30),  # Summer sale dates
            (7, 1), (7, 2), (7, 3), (7, 4), (7, 5)  # Winter sale dates
        ],
        # Add other events as needed
    }

    # Create future dataframe for 365 days
    future = model.make_future_dataframe(periods=365)
    
    # Define retail events list from the keys
    retail_events = list(retail_event_dates.keys())
    
    # Initialize all event columns to 0
    for event in retail_events:
        event_key = event.lower().replace(' ', '_')
        future[event_key] = 0
        
        # If we have defined dates for this event
        if event_key in retail_event_dates:
            # For each date pattern in the event
            for month, day in retail_event_dates[event_key]:
                # Set to 1 where month and day match
                future.loc[
                    (future['ds'].dt.month == month) & 
                    (future['ds'].dt.day == day),
                    event_key
                ] = 1

    # Special handling for Black Friday (last Friday of November)
    future.loc[
        (future['ds'].dt.month == 11) &  # November
        (future['ds'].dt.day >= 23) &    # Can't be earlier than 23rd
        (future['ds'].dt.day <= 29) &    # Can't be later than 29th
        (future['ds'].dt.dayofweek == 4), # Friday
        'black_friday'
    ] = 1

    # Special handling for Cyber Monday (3 days after Black Friday)
    future.loc[
        (future['ds'].dt.month == 11) &  # November
        (future['ds'].dt.day >= 26) &    # Can't be earlier than 26th
        (future['ds'].dt.day <= 30) &    # Can't be later than 30th
        (future['ds'].dt.dayofweek == 0), # Monday
        'cyber_monday'
    ] = 1

    # Special handling for American Labor Day (first Monday in September)
    future.loc[
        (future['ds'].dt.month == 9) &   # September
        (future['ds'].dt.day <= 7) &     # Can't be later than 7th
        (future['ds'].dt.dayofweek == 0), # Monday
        'labor_day'
    ] = 1

    # Make predictions
    forecast = model.predict(future)
    
    # Save predictions using proper paths
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(
        os.path.join(paths.brand_dir, f'{paths.brand}_predictions.csv'), 
        index=False
    )
    print(f"Predictions saved to {paths.brand_dir}/{paths.brand}_predictions.csv")

if __name__ == "__main__":
    brand = "Industrie"
    train_model(brand)
