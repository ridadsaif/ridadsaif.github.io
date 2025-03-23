import logging
import datetime
import random
import pandas as pd
from pymongo import MongoClient
from google.cloud import bigquery

# Constants
PROJECT_ID = "your-gcp-project-id"
DATASET_NAME = "recommendation_dataset"
ENVIRONMENT = "prod"

def extract_data_from_bigquery(sql_query):
    """Extract data from BigQuery based on a SQL query."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    query_job = bq_client.query(sql_query)
    rows = query_job.result()
    return [dict(row.items()) for row in rows]

def formatted_date(days):
    """Format date to query data from the past N days."""
    date_n_days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
    return date_n_days_ago.strftime("%Y-%m-%d %H:%M:%S")

def find_optimum_epsilon(client_id):
    """Compute decayed epsilon for explore-exploit."""
    epsilon = 0.5
    epsilon_query = f"""
    SELECT request_timestamp 
    FROM `{DATASET_NAME}.All_Interactions`
    WHERE client_id='{client_id}'
    ORDER BY request_timestamp ASC
    LIMIT 1
    """
    result = extract_data_from_bigquery(epsilon_query)
    if result:
        oldest_record = result[0]["request_timestamp"]
        days_difference = (datetime.datetime.now(datetime.timezone.utc) - oldest_record).days
        decayed_epsilon = epsilon / (1 + days_difference)
    else:
        decayed_epsilon = epsilon
    return decayed_epsilon

def explore_first_time(df, valid_rewards, db):
    """Explore new content from the top 75th percentile."""
    reward_values = list(valid_rewards.values())
    reward_urls = list(valid_rewards.keys())
    df_rewards = pd.DataFrame({'url': reward_urls, 'clicks': reward_values})
    threshold = df_rewards["clicks"].quantile(0.75)
    filtered_df = df_rewards[df_rewards["clicks"] >= threshold]
    
    if not filtered_df.empty:
        random_url = filtered_df.sample()["url"].values[0]
        reco_content = db.content.find_one({"url": random_url})
        return reco_content["_id"] if reco_content else None
    return None

def generate_mab(
    client_id,
    recommendation_sources,
    focus_content,
    slot_index,
    data,
    time_range,
    db
):
    """Main MAB Recommendation Logic."""
    df = data.copy()

    # Prepare rewards table
    rewards_table = df.set_index("url")["clicks"].to_dict()
    candidate_contents = list(db.content.find({"source": {"$in": recommendation_sources}}))
    
    # Filter valid URLs for rewards
    valid_rewards = {content["url"]: rewards_table[content["url"]] for content in candidate_contents if content["url"] in rewards_table}
    
    current_recommendations = focus_content.get("recommendations", [])
    
    # Check if MAB recommendations already exist
    mab_present = any(rec["model"] == "mab" for rec in current_recommendations)
    
    # Explore if no MAB recommendations are present
    if not mab_present:
        return explore_first_time(df, valid_rewards, db)
    
    # Explore-exploit phase if MAB already exists
    logging.info(f"Deciding between explore and exploit for slot #{slot_index}")
    decayed_epsilon = find_optimum_epsilon(client_id)
    
    toss = random.uniform(0, 1)
    if toss < decayed_epsilon:
        return explore_first_time(df, valid_rewards, db)
    
    # Exploit based on historical CTR
    expected_rewards = {url: rewards_table.get(url, 0) for url in valid_rewards}
    recommended_url = max(expected_rewards, key=expected_rewards.get, default=None)
    
    if recommended_url:
        reco_doc = db.content.find_one({"url": recommended_url})
        return reco_doc["_id"] if reco_doc else None
    return explore_first_time(df, valid_rewards, db)

def fetch_recommendations_mab(client_id, db, content_item_id, tag_name):
    """Fetch MAB-based recommendations and update content."""
    sql_query = f"""
    SELECT REGEXP_REPLACE(url, r'/$', '') as url, COUNT(*) as clicks
    FROM `{DATASET_NAME}.request`
    WHERE client_id='{client_id}'
    GROUP BY url
    ORDER BY clicks DESC
    """
    
    # Extract master data from BigQuery
    result = extract_data_from_bigquery(sql_query)
    data = pd.DataFrame(result)

    content_item = db.content.find_one({"_id": content_item_id})
    if not content_item:
        logging.error(f"Content {content_item_id} not found in DB.")
        return []

    content_recommendations = []
    slots = content_item.get("slots", [])

    for index, slot in enumerate(slots):
        recommendation_sources = slot.get("search_from", [])
        time_range = slot["date_config"]["value"]
        
        if recommendation_sources:
            reco_id = generate_mab(
                client_id,
                recommendation_sources,
                content_item,
                index,
                data,
                time_range,
                db
            )
            content_recommendations.append(reco_id)

    # Update recommendations in MongoDB
    if content_recommendations:
        recommendations = {
            "model": "mab",
            "version": tag_name,
            "client_id": client_id,
            "read_next": content_recommendations,
        }
        db.content.update_one(
            {"_id": content_item["_id"]},
            {"$set": {"recommendations": recommendations, "last_update.mab_recommendations": datetime.datetime.utcnow()}}
        )

    return content_recommendations
