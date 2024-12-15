import pandas as pd
from prophet import Prophet

data = pd.read_csv('terra-tonics/preppedTerratonicsDataset.csv')

# Create the main dataframe
data = {
    'ds': pd.to_datetime(data['post_date'], format='%d-%m-%Y'),
    'y': data['y'].astype(int),
    'likes': data['likesCount'],
    'comments': data['commentsCount'],
    'sale_date': pd.to_datetime(data['sale_date'], format='%d-%m-%Y')
}
df = pd.DataFrame(data)

# Create a holidays dataframe for sales events
sales_events = data[data['event'].notna()].copy()
holidays = pd.DataFrame({
    'holiday': 'sale_event',
    'ds': pd.to_datetime(sales_events['sale_date'], format='%d-%m-%Y'),
    'lower_window': -7,  # Start effect 7 days before
    'upper_window': 2    # Continue effect 2 days after
})

# Add regressors and events to the model
model = Prophet(holidays=holidays)
model.add_regressor('likes')
model.add_regressor('comments')

# Fit the model
model.fit(df)

# For future predictions, we need to include the regressor values
future = model.make_future_dataframe(periods=365)
# Add future values for regressors (you might want to use average or recent values)
future['likes'] = df['likes'].mean()  # Using mean as placeholder
future['comments'] = df['comments'].mean()  # Using mean as placeholder

# Make predictions
forecast = model.predict(future)

# Extract brand name from input filename
input_file = 'white-fox/preppedWhite-foxDataset.csv'
brand_name = input_file.split('prepped')[1].split('Dataset')[0]

# Save predictions to a CSV using the extracted brand name in camelCase
forecast[['ds', 'yhat']].to_csv(f'{brand_name.lower()}Prediction.csv', index=False)
print(f"Predictions saved to {brand_name.lower()}Prediction.csv")
