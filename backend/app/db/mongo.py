import os
from pymongo import MongoClient

class MongoDBMemory:
    def __init__(self): 
        mongo_client = MongoClient(os.getenv("CONNECTIONSTRING"))
        mongo_db = mongo_client["agent_memory"]
        mongo_collection = mongo_db["conversations"]
