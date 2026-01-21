from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MongoDBMemory:
    def __init__(self, session_id: str, user_id: str = "default_user"):
        conn_str = os.getenv("CONNECTIONSTRING")
        if not conn_str:
            raise ValueError("CONNECTIONSTRING environment variable is not set")
        self.client = MongoClient(conn_str)
        self.db = self.client["agent_memory"]
        self.collection = self.db["conversations"]
        self.profile_collection = self.db["user_profiles"]
        self.session_id = session_id
        self.user_id = user_id

    def get_user_profile(self) -> dict:
        doc = self.profile_collection.find_one({"user_id": self.user_id})
        return doc.get("profile", {}) if doc else {}

    def update_user_profile(self, info: any):
        current_profile = self.get_user_profile()
        if isinstance(info, dict):
            current_profile.update(info)
        else:
            current_profile["info"] = info
            
        self.profile_collection.update_one(
            {"user_id": self.user_id},
            {"$set": {"profile": current_profile, "last_updated": datetime.utcnow()}},
            upsert=True
        )

    def get_conversation(self) -> str:
        doc = self.collection.find_one({"session_id": self.session_id})
        if doc:
            return doc.get("conversation", "")
        return ""

    def save_conversation(self, conversation: str):
        self.collection.update_one(
            {"session_id": self.session_id},
            {
                "$set": {
                    "session_id": self.session_id,
                    "user_id": self.user_id,
                    "conversation": conversation,
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )

    def delete_session(self):
        self.collection.delete_one({"session_id": self.session_id})

    @classmethod
    def list_all_sessions(cls):
        client = MongoClient(os.getenv("CONNECTIONSTRING"))
        collection = client["agent_memory"]["conversations"]
        return list(collection.find({}, {"session_id": 1, "user_id": 1, "conversation": 1, "last_updated": 1}))
