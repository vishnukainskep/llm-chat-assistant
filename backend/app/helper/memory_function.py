from app.core.llm import llm
from app.db.db import MongoDBMemory
from langchain_classic.memory import ConversationSummaryMemory

class MemoryFunction:
    def __init__(self, session_id: str, user_id: str):
        self.db = MongoDBMemory(session_id, user_id)
        self.memory = ConversationSummaryMemory(llm=llm, memory_key="chat_summary")
        
    def load_history(self) -> str:
        return self.db.get_conversation()

    def add_message(self, role: str, content: str):
        current_history = self.load_history()
        new_entry = f"{role}: {content}\n"
        updated_history = current_history + new_entry
        self.db.save_conversation(updated_history)
        
    def get_summary(self) -> str:
        """
        Returns a summary of the conversation using ConversationSummaryMemory.
        """
        full_history = self.load_history()
        if not full_history:
            return ""
            
        self.memory.clear()
        for line in full_history.split("\n"):
            if line.startswith("user: "):
                self.memory.chat_memory.add_user_message(line.replace("user: ", ""))
            elif line.startswith("assistant: "):
                self.memory.chat_memory.add_ai_message(line.replace("assistant: ", ""))
        
        memory_vars = self.memory.load_memory_variables({})
        return memory_vars.get("chat_summary", "")

    def get_short_term_history(self, window_size: int = 5) -> str:
        """
        Returns the last 'window_size' messages from the history.
        This is the true 'short-term' memory.
        """
        full_history = self.load_history()
        if not full_history:
            return ""
            
        lines = [l for l in full_history.split("\n") if l.strip()]
        last_lines = lines[-window_size:]
        return "\n".join(last_lines)

    def get_full_context(self) -> str:
        """
        Combines summary of old messages with exact recent messages and user profile.
        """
        summary = self.get_summary()
        short_term = self.get_short_term_history(window_size=6)
        profile = self.db.get_user_profile()
        
        context = ""
        if profile:
            context += f"User Profile (Long-Term Memory): {profile}\n\n"
        if summary:
            context += f"Previous Conversation Summary: {summary}\n\n"
        if short_term:
            context += f"Recent Messages:\n{short_term}"
            
        return context if context else "No previous history."

    def update_profile(self, info: dict):
        self.db.update_user_profile(info)
