# Data Pipeline Instructions

Here's how to use this data pipeline:

1. Scrape a brand's Instagram page via Instagram scraping tool
2. Get the CSV and rename it "[brandname]Dataset.csv" (e.g. "gymsharkDataset.csv") 
3. Run that file through `sortPosts.py` to get a formatted dataset called "prepped[brandname]Dataset.csv"
4. Run that through `train_model.py` to get the prediction output in "[brandname]Prediction.csv"

The pipeline will:
- Process raw Instagram post data
- Extract sale information and events
- Train a Prophet model on the data
- Generate sale predictions for the next year
