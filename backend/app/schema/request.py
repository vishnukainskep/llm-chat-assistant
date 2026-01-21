from pydantic import BaseModel

class QueryRequest(BaseModel):
    user_input: str
    session_id: str | None = None
    user_id: str | None = "default_user"
