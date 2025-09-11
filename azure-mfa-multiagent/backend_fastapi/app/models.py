from pydantic import BaseModel
from typing import Optional

class UserInDB(BaseModel):
    id: str
    email: str
    password_hash: bytes
    azure_person_id: Optional[str] = None
    azure_speaker_profile_id: Optional[str] = None
    is_enrolled_face: bool = False
    is_enrolled_voice: bool = False

# Very small in-memory DB for demo. Replace with real DB (Postgres, etc.)
class SimpleDB:
    def __init__(self):
        self._by_email = {}
    def get_by_email(self, email: str):
        return self._by_email.get(email.lower())
    def save(self, user: UserInDB):
        self._by_email[user.email.lower()] = user
        return user
