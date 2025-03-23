import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import time
import openai

# Set OpenAI API key
def set_openai_key(api_key):
    openai.api_key = api_key

# Scrape competitor product data
def scrape_product_data(url):
    """Simulated product data extraction from a mock e-commerce site."""
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        product_data = [
            {"product_name": "Running Shoes", "price": 49.99, "features": "Lightweight, breathable"},
            {"product_name": "Yoga Mat", "price": 19.99, "features": "Non-slip, eco-friendly"},
        ]
        return pd.DataFrame(product_data)
    else:
        print(f"Failed to fetch data from {url}")
        return pd.DataFrame([])

# Generate search terms using LLM
def get_search_terms(product_description):
    prompt = f"""
    Extract core product terms from the following description:
    {product_description}
    Just return a comma-separated list of terms.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in generating search terms."},
            {"role": "user", "content": prompt}
        ]
    )
    response_text = response['choices'][0]['message']['content']
    return [term.strip() for term in response_text.split(',')]

# Match and analyze products
def match_and_analyze_products(product_info, competitor_data):
    """Compare Decathlon product data with competitor data."""
    matched_products = []
    for _, row in competitor_data.iterrows():
        if any(term in row['product_name'].lower() for term in product_info['search_terms']):
            matched_products.append({
                "competitor_product": row['product_name'],
                "price": row['price'],
                "features": row['features']
            })
    return matched_products
