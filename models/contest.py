from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List, Literal, Optional, Union

class UserSubscription(BaseModel):
    user: Union[int, str]

class ContestModel(BaseModel):
    id: str
    type: str
    amount_photo: Optional[int] = None
    amount_video: Optional[int] = None
    amount_text: Optional[int] = None
    title: str
    description: str
    img: str = "https://i.pinimg.com/originals/50/e6/79/50e679b4d2a6195d10deaa80d738d3b3.jpg"
    status: Literal["active", "inactive", "closed"] = "active"
    start_date: Optional[int] = None
    end_date: int
    subscription: Optional[List[UserSubscription]] = None
    created_by: int
    disqualified: Optional[List[UserSubscription]] = None

    class Config:
        orm_mode = True
        json_encoders = {ObjectId: str}
