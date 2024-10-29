from pydantic import BaseModel
from bson import ObjectId

class ContestModel(BaseModel):
    _id: str
    type: str
    amount_photo: int | None = None
    amount_video: int | None = None
    amount_text: int | None = None
    title: str
    description: str
    img: str | None = "https://i.pinimg.com/originals/50/e6/79/50e679b4d2a6195d10deaa80d738d3b3.jpg"
    status: str
    start_date: int | None = None
    end_date: int
    subscription: list[int] | None = None
    created_by: int

    class Config:
        orm_mode = True
        json_encoders = {ObjectId: str}
  