import pandas as pd
from prophet import Prophet
import os
from datetime import datetime
from dataCleaning import DataPaths

def train_model(brand: str):
    # Initialize paths and read data
    paths = DataPaths(brand)
    data = pd.read_csv(paths.prophet_data)
    
    # Create main dataframe
    df = pd.DataFrame({
        'ds': pd.to_datetime(data['snapshot'].astype(str), format='%Y%m%d%H%M%S'),
        'y': data['y'].astype(int)
    })
    
    # Create custom holiday dataframe for recurring sales patterns
    sales_patterns = pd.DataFrame([
        # Seasonal Sales (June/July and December/January)
        {'holiday': 'seasonal_sale', 'ds': pd.to_datetime('2023-12-23'), 'lower_window': 0, 'upper_window': 7},  # End of year
        {'holiday': 'seasonal_sale', 'ds': pd.to_datetime('2023-06-28'), 'lower_window': 0, 'upper_window': 32}, # Mid year
        {'holiday': 'seasonal_sale', 'ds': pd.to_datetime('2022-12-27'), 'lower_window': 0, 'upper_window': 7},
        {'holiday': 'seasonal_sale', 'ds': pd.to_datetime('2022-07-23'), 'lower_window': 0, 'upper_window': 2},
        {'holiday': 'seasonal_sale', 'ds': pd.to_datetime('2021-06-15'), 'lower_window': 0, 'upper_window': 0},
        {'holiday': 'seasonal_sale', 'ds': pd.to_datetime('2020-06-26'), 'lower_window': 0, 'upper_window': 0},
        {'holiday': 'seasonal_sale', 'ds': pd.to_datetime('2019-07-04'), 'lower_window': 0, 'upper_window': 0},
        {'holiday': 'seasonal_sale', 'ds': pd.to_datetime('2024-12-24'), 'lower_window': 0, 'upper_window': 6},
        
        # Friends and Family
        {'holiday': 'friends_and_family', 'ds': pd.to_datetime('2023-03-14'), 'lower_window': 0, 'upper_window': 5},
        {'holiday': 'friends_and_family', 'ds': pd.to_datetime('2023-06-28'), 'lower_window': 0, 'upper_window': 32},
        {'holiday': 'friends_and_family', 'ds': pd.to_datetime('2023-08-04'), 'lower_window': 0, 'upper_window': 1},
        {'holiday': 'friends_and_family', 'ds': pd.to_datetime('2023-08-11'), 'lower_window': 0, 'upper_window': 1},
        {'holiday': 'friends_and_family', 'ds': pd.to_datetime('2023-08-18'), 'lower_window': 0, 'upper_window': 0},
        
        # Other sales patterns
        {'holiday': 'flash_sale', 'ds': pd.to_datetime('2023-09-04'), 'lower_window': 0, 'upper_window': 0},
        {'holiday': 'generic_sale', 'ds': pd.to_datetime('2024-06-27'), 'lower_window': 0, 'upper_window': 4},
        {'holiday': 'outlet_sale', 'ds': pd.to_datetime('2020-03-17'), 'lower_window': 0, 'upper_window': 1},
        {'holiday': 'outlet_sale', 'ds': pd.to_datetime('2024-02-17'), 'lower_window': 0, 'upper_window': 0},
    ])
    
    # Add biannual seasonal windows
    seasonal_windows = pd.DataFrame([
        # Mid-year seasonal window (June-July)
        *[{'holiday': 'seasonal_window', 'ds': pd.to_datetime(f'2023-06-{day}'), 'lower_window': 0, 'upper_window': 0} for day in range(15, 31)],
        *[{'holiday': 'seasonal_window', 'ds': pd.to_datetime(f'2023-07-{day}'), 'lower_window': 0, 'upper_window': 0} for day in range(1, 16)],
        
        # End-year seasonal window (December-January)
        *[{'holiday': 'seasonal_window', 'ds': pd.to_datetime(f'2023-12-{day}'), 'lower_window': 0, 'upper_window': 0} for day in range(15, 32)],
        *[{'holiday': 'seasonal_window', 'ds': pd.to_datetime(f'2024-01-{day}'), 'lower_window': 0, 'upper_window': 0} for day in range(1, 16)],
    ])
    
    # Combine all patterns
    all_patterns = pd.concat([sales_patterns, seasonal_windows], ignore_index=True)
    
    # Initialize model with holidays
    model = Prophet(
        changepoint_prior_scale=0.001,
        yearly_seasonality=20,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_prior_scale=10,
        holidays_prior_scale=20,
        holidays=all_patterns
    )
    
    # Add custom seasonality patterns
    model.add_seasonality(name='biannual', period=182.5, fourier_order=10)
    model.add_seasonality(name='quarterly', period=91.25, fourier_order=5)
    
    # Create seasonal intensity for training data
    df['seasonal_intensity'] = ((df['ds'].dt.month.isin([6, 7, 12, 1])) & 
                               (df['ds'].dt.day >= 15) & 
                               (df['ds'].dt.day <= 31)).astype(int)
    
    # Add regressor before fitting
    model.add_regressor('seasonal_intensity')
    
    # Fit model first
    model.fit(df)
    
    # Now create future dataframe after model is fit
    future = model.make_future_dataframe(periods=365)
    
    # Add seasonal intensity to future data
    future['seasonal_intensity'] = ((future['ds'].dt.month.isin([6, 7, 12, 1])) & 
                                  (future['ds'].dt.day >= 15) & 
                                  (future['ds'].dt.day <= 31)).astype(int)
    
    # Make predictions
    forecast = model.predict(future)
    
    # Save predictions
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(
        os.path.join(paths.brand_dir, f'{paths.brand}_predictions.csv'), 
        index=False
    )
    print(f"Predictions saved to {paths.brand_dir}/{paths.brand}_predictions.csv")

if __name__ == "__main__":
    brand = "Gymshark"
    train_model(brand)
