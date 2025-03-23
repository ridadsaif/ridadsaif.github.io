import openai
import pandas as pd
import re

# Set OpenAI API key
def set_openai_key(api_key):
    openai.api_key = api_key

# Compare product descriptions and generate similarity score
def compare_products(product1_info, product2_info):
    """Compare two products using NLP and assign a similarity score."""
    prompt = f"""
    Compare the following two product descriptions:

    Product 1: {product1_info}
    Product 2: {product2_info}

    Identify similarities in terms of features, target audience, and intended use.
    Return a similarity score as a percentage, along with key insights.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in product analysis and comparison."},
            {"role": "user", "content": prompt}
        ]
    )
    result = response['choices'][0]['message']['content']
    score_match = re.search(r"Score\s*:\s*(\d+)", result)
    score = int(score_match.group(1)) if score_match else None
    return result, score

# Main workflow
def main_comparator():
    decathlon_product_info = "Trail Running Shoes: Breathable and lightweight trail running shoes designed for all terrains."

    competitor_data = pd.read_csv("../data/sample_products.csv")
    for _, row in competitor_data.iterrows():
        competitor_info = f"{row['product_name']}: {row['features']}"
        comparison_result, similarity_score = compare_products(decathlon_product_info, competitor_info)
        print(f"Comparison Result: {comparison_result}")
        print(f"Similarity Score: {similarity_score}%")

# Run comparator
if __name__ == "__main__":
    main_comparator()
