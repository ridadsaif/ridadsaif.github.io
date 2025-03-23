from pymongo import MongoClient
import os

def get_db(secret_id):
    """Connects to MongoDB using the provided secret ID."""
    db_url = os.environ.get(secret_id)
    client = MongoClient(db_url)
    return client.get_database()
