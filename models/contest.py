from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List, Optional

class UserSubscription(BaseModel):
    user: str = Field(..., alias="$numberLong")

class ContestModel(BaseModel):
    _id: str
    type: str
    amount_photo: Optional[int] = None
    amount_video: Optional[int] = None
    amount_text: Optional[int] = None
    title: str
    description: str
    img: str = "https://i.pinimg.com/originals/50/e6/79/50e679b4d2a6195d10deaa80d738d3b3.jpg"
    status: str
    start_date: Optional[int] = None
    end_date: int
    subscription: Optional[List[UserSubscription]] = None
    created_by: int
    disqualified: Optional[List[UserSubscription]] = None

    class Config:
        orm_mode = True
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True
