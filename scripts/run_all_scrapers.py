import subprocess
import os
import re
import pandas as pd
import boto3
from datetime import datetime

def run_notebook(notebook_path):
    result = subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", notebook_path], capture_output=True)
    if result.returncode != 0:
        print(f"Error executing {notebook_path}:\n{result.stderr.decode('utf-8')}")

def sanitize_brand_name(brand_name):
    sanitized_name = re.sub(r"[^\w\s]", "", brand_name).replace(" ", "_")
    return sanitized_name.lower()

def upload_to_s3(local_path, s3_path, bucket_name):
    s3 = boto3.client('s3')
    s3.upload_file(local_path, bucket_name, s3_path)

def update_readme():
    readme_path = "README.md"
    data_path = "data/brands/"
    archive_path = "data/archive/"
    brands_info = [
        {"name": "Brandy Melville", "parent": "Marsan Family", "notebook": "brandy_melville/fetch_products.ipynb"},
        {"name": "Heinz", "parent": "The Kraft Heinz Co.", "notebook": "heinz/fetch_products.ipynb"},
        {"name": "La Croix", "parent": "National Beverage Corp.", "notebook": "la_croix/fetch_products.ipynb"},
        {"name": "Buldak", "parent": "Samyang America, Inc.", "notebook": "buldak/fetch_products.ipynb"},
        {"name": "Ottogi", "parent": "Ottogi Corporation", "notebook": "ottogi/fetch_products.ipynb"},
        {"name": "Raos", "parent": "Campbell Soup Company", "notebook": "raos/fetch_products.ipynb"}
    ]

    readme_content = [
        "# Products",
        "",
        "## About",
        "The repo contains scrapers that fetch product information from popular brands. It's a non-commercial sandbox to practice web scraping.",
        "",
        "## Process",
        "The data are collected from each brand's website with Python and Jupyter Lab notebooks stored in the `notebooks/brand_scrapers` directory.",
        "",
        "## Brands collected",
        "",
        "| Notebook                | Parent                | Files   | Product Count   |",
        "| :---------------------- | :-------------------- | :------ | :-------------- |"
    ]

    for brand in brands_info:
        sanitized_name = sanitize_brand_name(brand['name'])
        csv_path = os.path.join(data_path, f"{sanitized_name}.csv")
        json_path = os.path.join(data_path, f"{sanitized_name}.json")
        timestamp = datetime.now().strftime("%Y%m%d")
        archive_csv_path = os.path.join(archive_path, f"{sanitized_name}_{timestamp}.csv")
        archive_json_path = os.path.join(archive_path, f"{sanitized_name}_{timestamp}.json")
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            product_count = len(df)
            
            # Archive current data
            os.makedirs(archive_path, exist_ok=True)
            df.to_csv(archive_csv_path, index=False)
            df.to_json(archive_json_path, orient="records")

            # Upload to S3
            upload_to_s3(archive_csv_path, f"products/data/archive/{sanitized_name}_{timestamp}.csv", os.getenv("AWS_S3_BUCKET"))
            upload_to_s3(archive_json_path, f"products/data/archive/{sanitized_name}_{timestamp}.json", os.getenv("AWS_S3_BUCKET"))

            readme_content.append(f"| [{brand['name']}](https://github.com/stiles/products/blob/main/notebooks/brand_scrapers/{brand['notebook']}) | {brand['parent']} | [json](https://stilesdata.com/products/data/{sanitized_name}.json), [csv](https://stilesdata.com/products/data/{sanitized_name}.csv) | {product_count} |")
        else:
            readme_content.append(f"| [{brand['name']}](https://github.com/stiles/products/blob/main/notebooks/brand_scrapers/{brand['notebook']}) | {brand['parent']} | [json](https://stilesdata.com/products/data/{sanitized_name}.json), [csv](https://stilesdata.com/products/data/{sanitized_name}.csv) | N/A |")

    with open(readme_path, 'w') as f:
        f.write("\n".join(readme_content))

def main():
    base_path = "notebooks/brand_scrapers/"
    brands = ["brandy_melville", "buldak", "heinz", "la_croix", "ottogi", "raos"]

    for brand in brands:
        notebook_path = os.path.join(base_path, brand, "fetch_products.ipynb")
        print(f"Running scraper for {brand}")
        run_notebook(notebook_path)
    
    update_readme()

if __name__ == "__main__":
    main()