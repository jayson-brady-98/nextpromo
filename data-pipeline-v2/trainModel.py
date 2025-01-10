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
    
    # Initialize and configure model with simplified parameters
    model = Prophet(
        yearly_seasonality=20,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_prior_scale=15,
        changepoint_prior_scale=0.05
    )
    
    # Fit model
    model.fit(df)
    
    # Create future dataframe for 365 days
    future = model.make_future_dataframe(periods=365)
    
    # Make predictions
    forecast = model.predict(future)
    
    # Save predictions using proper paths
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(
        os.path.join(paths.brand_dir, f'{paths.brand}_predictions.csv'), 
        index=False
    )
    print(f"Predictions saved to {paths.brand_dir}/{paths.brand}_predictions.csv")

if __name__ == "__main__":
    brand = "Gymshark"
    train_model(brand)
