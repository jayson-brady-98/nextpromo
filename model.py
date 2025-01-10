import pandas as pd
from prophet import Prophet

def train_model(brand: str):
    # Read the data from the correct path
    data = pd.read_csv(f'newData/{brand}/p_{brand}.csv')
    
    # Create main dataframe for Prophet
    df = pd.DataFrame({
        'ds': pd.to_datetime(data['snapshot'].astype(str), format='%Y%m%d%H%M%S'),
        'y': data['y'].astype(int)
    })
    
    # Initialize and configure model
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
    
    # Save predictions
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(
        f'{brand}_predictions.csv', 
        index=False
    )

if __name__ == "__main__":
    brand = "Gymshark"
    train_model(brand)
