from datetime import datetime
from pydantic import Field, EmailStr, BaseModel, field_validator


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=20)
    description: str = Field(min_length=3, max_length=50)
    deadline: datetime


class TaskUpdate(BaseModel):
    title: str | None = Field(None,min_length=3, max_length=20)
    description: str | None = Field(None,min_length=3, max_length=50)
    deadline: datetime | None = None
