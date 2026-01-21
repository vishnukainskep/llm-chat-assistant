from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
import os
from datetime import datetime

router = APIRouter()

def get_collection():
    client = MongoClient(os.getenv("CONNECTIONSTRING"))
    return client["agent_memory"]["conversations"]

@router.get("/sessions")
async def list_sessions():
    collection = get_collection()
    # Fetch all sessions, handle both session_id and SessionId for backward compatibility
    sessions = list(collection.find({}, {
        "session_id": 1, 
        "SessionId": 1,
        "user_id": 1, 
        "conversation": 1, 
        "History": 1,
        "last_updated": 1
    }).sort("last_updated", -1))
    
    session_list = []
    for s in sessions:
        sid = s.get("session_id") or s.get("SessionId") or str(s.get("_id"))
        user_id = s.get("user_id", "unknown")
        
        # Extract title from conversation (new format) or History (old format)
        title = "New Chat"
        conv = s.get("conversation", "")
        if conv:
            lines = [l for l in conv.split("\n") if l.strip()]
            if lines:
                first_line = lines[0]
                if first_line.startswith("user: "):
                    title = first_line.replace("user: ", "")[:40]
                else:
                    title = first_line[:40]
        else:
            # Fallback to old History format if available
            history = s.get("History", [])
            if history and isinstance(history, list) and len(history) > 0:
                first_msg = history[0]
                if isinstance(first_msg, dict):
                    title = first_msg.get("content", "New Chat")[:40]
        
        session_list.append({
            "id": sid, 
            "user_id": user_id,
            "title": title,
            "last_updated": s.get("last_updated").isoformat() if isinstance(s.get("last_updated"), datetime) else s.get("last_updated")
        })
        
    return {"sessions": session_list}

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    collection = get_collection()
    # Delete by session_id or SessionId
    collection.delete_many({"$or": [{"session_id": session_id}, {"SessionId": session_id}]})
    return {"status": "deleted"}

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    collection = get_collection()
    # Find by session_id or SessionId
    doc = collection.find_one({"$or": [{"session_id": session_id}, {"SessionId": session_id}]})
    
    if not doc:
        return {"history": []}
    
    messages = []
    
    # Check new format first
    conv = doc.get("conversation", "")
    if conv:
        for line in conv.split("\n"):
            if line.startswith("user: "):
                messages.append({"type": "human", "content": line.replace("user: ", "")})
            elif line.startswith("assistant: "):
                messages.append({"type": "ai", "content": line.replace("assistant: ", "")})
    else:
        # Fallback to old History format
        history = doc.get("History", [])
        if history and isinstance(history, list):
            for msg in history:
                if isinstance(msg, dict):
                    # Handle both LangChain message objects and simple dicts
                    m_type = msg.get("type") or msg.get("role")
                    content = msg.get("content") or msg.get("text")
                    if m_type in ["human", "user"]:
                        messages.append({"type": "human", "content": content})
                    elif m_type in ["ai", "assistant"]:
                        messages.append({"type": "ai", "content": content})
            
    return {"history": messages}
