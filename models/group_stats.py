from pydantic import BaseModel, Field
from typing import List

class Members(BaseModel):
    current: int
    previous: int

class Viewers(BaseModel):
    current: int
    previous: int

class Messages(BaseModel):
    current: int
    previous: int

class Posters(BaseModel):
    current: int
    previous: int

class Period(BaseModel):
    min_date: int  # Unix timestamp (en segundos)
    max_date: int  # Unix timestamp (en segundos)

class TopAdmin(BaseModel):
    user_id: int
    first_name: str | None
    deleted: int
    kicked: int
    banned: int

class TopUser(BaseModel):
    user_id: int
    first_name: str | None
    messages: int
    avg_chars: int

class StatsDaily(BaseModel):
    _id: str  # MongoDB uses _id as the primary key
    members: Members
    viewers: Viewers
    messages: Messages
    period: Period
    posters: Posters
    top_admins: List[TopAdmin]
    top_users: List[TopUser]
