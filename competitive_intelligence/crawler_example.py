import requests
from bs4 import BeautifulSoup
import pandas as pd
import openai
import time

# Set OpenAI API key
def set_openai_key(api_key):
    openai.api_key = api_key

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

# Scrape product data from competitor website
def scrape_competitor_data(search_term):
    """Simulate web scraping using a mock competitor search."""
    base_url = f"https://mock-competitor-site.com/search?q={search_term}"
    response = requests.get(base_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        product_data = [
            {"product_name": f"{search_term} Shoes", "price": 49.99, "features": "Lightweight, breathable"},
            {"product_name": f"{search_term} Mat", "price": 19.99, "features": "Non-slip, eco-friendly"}
        ]
        return pd.DataFrame(product_data)
    else:
        print(f"Failed to fetch data for {search_term}")
        return pd.DataFrame([])

# Main workflow
def main_scraper():
    decathlon_product_info = {
        "product_name": "Trail Running Shoes",
        "description": "Breathable and lightweight trail running shoes designed for all terrains."
    }

    search_terms = get_search_terms(decathlon_product_info['description'])
    all_competitor_data = pd.DataFrame([])

    for term in search_terms:
        competitor_data = scrape_competitor_data(term)
        all_competitor_data = pd.concat([all_competitor_data, competitor_data], ignore_index=True)

    print("Scraped Competitor Data:", all_competitor_data)
    all_competitor_data.to_csv("../data/sample_products.csv", index=False)

# Run scraper
if __name__ == "__main__":
    main_scraper()
