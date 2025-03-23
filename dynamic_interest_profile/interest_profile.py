from pymongo import ASCENDING, DESCENDING
from collections import Counter
import operator
import math
import os
from src.db_connector import get_db
from src.config import SIM_MODELS, RELEVANCE_MODELS, LIMIT_KEYWORDS, ALPHA

# MongoDB Connections
db = get_db(secret_id="DB_SECRET_ID")
db_user_data = get_db(secret_id="DB_SECRET_ID_USER_DATA")

def standardize(weights):
    """Normalizes weights to ensure sum equals 1."""
    total = sum(weights.values())
    if total == 0:
        return weights
    return {k: v / total for k, v in weights.items()}


def create_new_interest_profile(current_content, weights, interest_profile_list):
    """Generates a new interest profile by merging old and new content."""
    weights = standardize(weights)
    entities = current_content.get("entities", [])
    subjects = current_content.get("subjects", [])
    relevance = {}

    # Collect relevance and qcode mapping
    label_to_qcode = {}
    for entity in entities:
        if entity["qcode"] in subjects:
            relevance[entity["label"]] = entity.get("relevance", 0)
        label_to_qcode[entity["label"]] = entity["qcode"]

    # Merge old and new profiles
    for keyword, score in relevance.items():
        if keyword in weights:
            weights[keyword] += score
        else:
            weights[keyword] = score

    # Select top-ranked entities for the new profile
    ranked_keywords = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    selected_keywords = dict(ranked_keywords[:LIMIT_KEYWORDS])

    # Generate modified profile
    modified_interest_profile_list = [
        {"label": k, "weight": v, "qcode": label_to_qcode[k]} for k, v in selected_keywords.items()
    ]

    return modified_interest_profile_list


def update_interest_profile(user_id, url, first_time=True):
    """Updates the user's interest profile dynamically."""
    user_item = db_user_data.user_profile.find_one({"user_id": user_id})

    if first_time:
        content = db.content.find_one({"url": url})
        entities = content.get("entities", [])
        interest_profile_list = []

        # Initialize interest profile with top 3 subjects
        for entity in entities:
            if entity["qcode"] in content.get("subjects", [])[:3]:
                interest_profile_list.append({
                    "qcode": entity["qcode"],
                    "weight": entity.get("relevance", 0),
                    "label": entity["label"]
                })

        db_user_data.user_profile.update_one(
            {"user_id": user_id},
            {"$set": {"interest_profile": interest_profile_list}},
            upsert=True,
        )
    else:
        # Load existing profile and update it
        existing_profile = user_item.get("interest_profile", [])
        weights = {entry["label"]: entry["weight"] for entry in existing_profile}
        current_content = db.content.find_one({"url": url})

        modified_interest_profile_list = create_new_interest_profile(
            current_content, weights, existing_profile
        )

        db_user_data.user_profile.update_one(
            {"user_id": user_id},
            {"$set": {"interest_profile": modified_interest_profile_list}},
        )
