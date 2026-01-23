from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class MongoDBMemory:
    def __init__(self, session_id: str, user_id: str = "default_user"):
        conn_str = os.getenv("CONNECTIONSTRING")
        if not conn_str:
            raise ValueError("CONNECTIONSTRING environment variable is not set")

        self.client = MongoClient(conn_str)
        db = self.client["agent_memory"]

        self.conversations = db["conversations"]
        self.user_profiles = db["user_profiles"]

        self.session_id = session_id
        self.user_id = user_id

    # ---------- User profile ----------

    def get_user_profile(self) -> dict:
        doc = self.user_profiles.find_one({"user_id": self.user_id})
        return doc.get("profile", {}) if doc else {}

    def update_user_profile(self, info):
        profile = self.get_user_profile()

        if isinstance(info, dict):
            profile.update(info)
        else:
            profile["info"] = info

        self.user_profiles.update_one(
            {"user_id": self.user_id},
            {
                "$set": {
                    "profile": profile,
                    "last_updated": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    # ---------- Conversation ----------

    def get_conversation(self) -> str:
        doc = self.conversations.find_one({"session_id": self.session_id})
        return doc.get("conversation", "") if doc else ""

    def save_conversation(self, conversation: str):
        self.conversations.update_one(
            {"session_id": self.session_id},
            {
                "$set": {
                    "session_id": self.session_id,
                    "user_id": self.user_id,
                    "conversation": conversation,
                    "last_updated": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    def delete_session(self):
        self.conversations.delete_one({"session_id": self.session_id})

    # ---------- list all ----------

    @classmethod
    def list_all_sessions(cls):
        client = MongoClient(os.getenv("CONNECTIONSTRING"))
        collection = client["agent_memory"]["conversations"]
        return list(
            collection.find(
                {},
                {
                    "session_id": 1,
                    "user_id": 1,
                    "conversation": 1,
                    "last_updated": 1,
                },
            )
        )
