import logging
import datetime
import statistics
from helpers import (
    cosine_sim,
    counter_cosine_similarity,
    find_cosine_score,
    form_final_recommendations,
    get_named_entities,
)

def get_documents(content_db, time_range, sources, exclude_ids, fallback=False):
    """Fetch candidate documents with specified filters."""
    query = {
        "source": {"$in": sources},
        "_id": {"$nin": exclude_ids},
    }
    
    if not fallback:
        query["date"] = {"$gte": datetime.datetime.now() - datetime.timedelta(days=time_range)}

    return content_db.find(query).limit(50)

def generate_recommendations(content_id, content_db, sources, time_range):
    """Generate content-based recommendations."""
    base_content = content_db.find_one({"_id": content_id})
    documents = get_documents(content_db, time_range, sources, [content_id])

    # Step 1: Subject Matching (Simulate with Dummy Subject Logic)
    base_subjects = base_content.get("subjects", [])
    chosen_contents = [
        content for content in documents if any(sub in content.get("subjects", []) for sub in base_subjects)
    ]
    
    # Step 2: Named Entity Matching Fallback
    if not chosen_contents:
        logging.info("Fallback to Named Entity Matching")
        named_entities = get_named_entities(base_content)
        chosen_contents = [
            content for content in documents if any(
                entity.lower() in content.get("title", "").lower() for entity in named_entities
            )
        ]
    
    # Step 3: Scoring and Ranking
    scores = {}
    for content in chosen_contents:
        count_score = counter_cosine_similarity(base_content, content)
        cosine_score = find_cosine_score(base_content, content)
        tfidf_score = cosine_sim(base_content, content)
        
        # Average score from multiple metrics
        mean_score = statistics.mean([cosine_score, count_score, tfidf_score])
        scores[content["_id"]] = mean_score
    
    # Step 4: Return Best Recommendations
    return form_final_recommendations(scores)
