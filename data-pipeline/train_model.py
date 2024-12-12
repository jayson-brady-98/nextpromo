import pandas as pd
from prophet import Prophet

data = pd.read_csv('terra-tonics/preppedTerratonicsDataset.csv')
data = {
    'ds': pd.to_datetime(data['post_date'], format='%d-%m-%Y'),
    'y': data['y'].astype(int),
    'likes': data['likesCount'],
    'comments': data['commentsCount'],
    'sale_date': pd.to_datetime(data['sale_date'], format='%d-%m-%Y')
}
df = pd.DataFrame(data)

# Fit the model
model = Prophet()
model.fit(df)

# Forecast future dates (e.g., next 180 days)
future = model.make_future_dataframe(periods=365)  # Generate future dates
forecast = model.predict(future)

# Extract brand name from input filename
input_file = 'terra-tonics/preppedTerratonicsDataset.csv'
brand_name = input_file.split('prepped')[1].split('Dataset')[0]

# Save predictions to a CSV using the extracted brand name in camelCase
forecast[['ds', 'yhat']].to_csv(f'{brand_name.lower()}Prediction.csv', index=False)
print(f"Predictions saved to {brand_name.lower()}Prediction.csv")
