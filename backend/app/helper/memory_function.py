from app.core.llm import llm
from app.db.db import MongoDBMemory
from langchain_classic.memory import ConversationSummaryMemory


class MemoryFunction:
    def __init__(self, session_id: str, user_id: str):
        self.db = MongoDBMemory(session_id, user_id)
        self.summary_memory = ConversationSummaryMemory(
            llm=llm,
            memory_key="chat_summary"
        )

    # ---------- Basic storage ----------

    def load_history(self) -> str:
        return self.db.get_conversation() or ""

    def add_message(self, role: str, content: str):
        self.db.save_conversation(
            self.load_history() + f"{role}: {content}\n"
        )

    # ---------- Summarization ----------

    def get_summary(self) -> str:
        history = self.load_history()
        if not history:
            return ""

        self.summary_memory.clear()

        for line in history.splitlines():
            if line.startswith("user:"):
                self.summary_memory.chat_memory.add_user_message(
                    line.replace("user:", "").strip()
                )
            elif line.startswith("assistant:"):
                self.summary_memory.chat_memory.add_ai_message(
                    line.replace("assistant:", "").strip()
                )

        return self.summary_memory.load_memory_variables({}).get("chat_summary", "")

    # ---------- Short-term memory ----------

    def get_recent_messages(self, limit: int = 6) -> str:
        lines = [l for l in self.load_history().splitlines() if l.strip()]
        return "\n".join(lines[-limit:])

    # ---------- Context assembly ----------

    def get_full_context(self) -> str:
        parts = []

        profile = self.db.get_user_profile()
        if profile:
            parts.append(f"User Profile:\n{profile}")

        summary = self.get_summary()
        if summary:
            parts.append(f"Conversation Summary:\n{summary}")

        recent = self.get_recent_messages()
        if recent:
            parts.append(f"Recent Messages:\n{recent}")
        
        print(parts)

        return "\n\n".join(parts) if parts else "No previous history."

    # ---------- Long-term profile ----------

    def update_profile(self, info: dict):
        self.db.update_user_profile(info)
