from datetime import datetime, timezone
from pydantic import Field, EmailStr, BaseModel, field_validator

class DeadlineValidatorMixin:
    @field_validator("deadline")
    @classmethod
    def deadline_check(cls, v: datetime | None):
        if v is None:
            return v

        now = datetime.now(timezone.utc)
        target = v if v.tzinfo else v.replace(tzinfo=timezone.utc)

        if target <= now:
            raise ValueError("Делайн не может быть в прошлом")
        return v


class TaskCreate(BaseModel,DeadlineValidatorMixin):
    title: str = Field(min_length=3, max_length=20)
    description: str = Field(min_length=3, max_length=50)
    deadline: datetime


class TaskUpdate(BaseModel,DeadlineValidatorMixin):
    title: str | None = Field(None, min_length=3, max_length=20)
    description: str | None = Field(None, min_length=3, max_length=50)
    deadline: datetime | None = None
    status: bool | None = None

    
