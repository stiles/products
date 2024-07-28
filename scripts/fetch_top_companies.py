import os
import pandas as pd
from pathlib import Path
import boto3

"""
TOP 100 food companies in the US and Candada
According to foodprocess.com
"""

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

# Determine the absolute paths for input and output files
BASE = Path(__file__).resolve().parent
CSV_OUT = BASE / "../data/reference/top_food_companies.csv"
JSON_OUT = BASE / "../data/reference/top_food_companies.json"
MARKDOWN_OUT = BASE / "../data/reference/products.md"

url = 'https://www.foodprocessing.com/top100/2023'
# clean_url = 'https://www.foodprocessing.com/top100/2023/alpha'

src = pd.read_html(url, storage_options=headers)[0].dropna(subset='This Year')
src.columns = src.columns.str.lower().str.replace(' ', '_')

src['company'] = src['company'].str.split('(', expand=True)[0].str.strip()
src['2022_food_sales'] = src['2022_food_sales'].str.split(' ', expand=True)[0].str.strip()
src['2022_total_company_sales'] = src['2022_total_company_sales'].str.split(' ', expand=True)[0].str.strip()
src['this_year'] = src['this_year'].astype(int)
src['product_page_url'] = ''
src['product_count'] = ''

df = src.sort_values('this_year').dropna(subset='this_year').drop(['unnamed:_8', 'last_year', 
       '2021_food_sales', '2022_total_company_sales', '2022_food_sales',
       '2022_net_income*_(-loss)', '2021_net_income*_(-loss)'], axis=1).rename(columns={'this_year': 'rank'}).copy()

print(df.columns)

# Output local files
df.head(20).to_markdown(MARKDOWN_OUT, index=False)
df.to_csv(CSV_OUT, index=False)
df.to_json(JSON_OUT, indent=4, orient='records')

# Paths for S3 storage
S3_BUCKET = 'stilesdata.com'
S3_CSV_KEY = 'products/top_food_companies.csv'
S3_JSON_KEY = 'products/top_food_companies.json'

# Initialize boto3 client with environment variables
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('MY_AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('MY_AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('MY_AWS_SESSION_TOKEN')
)

# Upload the CSV file to S3
s3_client.upload_file(str(CSV_OUT), S3_BUCKET, S3_CSV_KEY)
print(f"CSV file uploaded to s3://{S3_BUCKET}/{S3_CSV_KEY}")

# Upload the JSON file
s3_client.upload_file(str(JSON_OUT), S3_BUCKET, S3_JSON_KEY)
print(f"JSON file uploaded to s3://{S3_BUCKET}/{S3_JSON_KEY}")