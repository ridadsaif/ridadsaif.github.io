import numpy as np
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

vectorizer = TfidfVectorizer(stop_words="english")

def normalize(text):
    """Normalize and tokenize text for vectorization."""
    return text.lower()

def cosine_sim(content1, content2):
    """TF-IDF Cosine Similarity between two content items."""
    tfidf = vectorizer.fit_transform([content1["text"], content2["text"]])
    return ((tfidf * tfidf.T).A)[0, 1]

def counter_cosine_similarity(content1, content2):
    """Cosine similarity using subject counters."""
    counter1 = Counter(content1.get("subjects", []))
    counter2 = Counter(content2.get("subjects", []))

    terms = set(counter1).union(counter2)
    dot_product = sum(counter1.get(term, 0) * counter2.get(term, 0) for term in terms)
    norm1 = sum(counter1.get(term, 0) ** 2 for term in terms)
    norm2 = sum(counter2.get(term, 0) ** 2 for term in terms)

    try:
        return dot_product / math.sqrt(norm1 * norm2)
    except ZeroDivisionError:
        return 0

def find_cosine_score(content1, content2):
    """Compute similarity using embeddings or fallback."""
    vector1 = np.random.rand(300)  # Simulated embedding
    vector2 = np.random.rand(300)
    
    cosine_score = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
    return round(cosine_score, 4)

def get_named_entities(content):
    """Extract named entities from the title."""
    title = content.get("title", "")
    return [word.lower() for word in title.split() if len(word) > 3]

def form_final_recommendations(scores):
    """Return highest scoring content as recommendations."""
    sorted_scores = sorted(scores, key=scores.get, reverse=True)
    if sorted_scores:
        best_content_id = sorted_scores[0]
        return best_content_id, scores[best_content_id]
    return None, None
