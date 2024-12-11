import pandas as pd
from prophet import Prophet

data = pd.read_csv('preppedGymsharkDataset.csv')
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

# Save predictions to a CSV
forecast[['ds', 'yhat']].to_csv('gymsharkPrediction.csv', index=False)
print("Predictions saved to gymsharkPrediction.csv")
