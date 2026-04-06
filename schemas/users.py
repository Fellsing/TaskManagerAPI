from pydantic import Field, EmailStr, BaseModel, field_validator, ConfigDict


class UserCreate(BaseModel):
    username:str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password:str = Field(min_length=8, max_length=30)

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="forbid")


