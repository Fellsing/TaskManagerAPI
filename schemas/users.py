from pydantic import Field, EmailStr, BaseModel, field_validator


class UserCreate(BaseModel):
    username:str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password:str = Field(min_length=8, max_length=30)


