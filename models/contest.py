from bson import ObjectId
from pydantic import BaseModel, ConfigDict, PlainSerializer, Field
from typing import Annotated, List, Literal, Optional, Union

PyObjectId = Annotated[
    ObjectId,
    PlainSerializer(lambda x: str(x), return_type=str)
]

class UserSubscription(BaseModel):
    user: Union[int, str]

class ContestModel(BaseModel):
    id: PyObjectId
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

    model_config = ConfigDict(from_attributes=True)
