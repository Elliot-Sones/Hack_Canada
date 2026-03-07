from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterRequest(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=200)
    organization_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str = Field(min_length=1, max_length=128)


class UserInfo(BaseModel):
    id: str
    email: str
    name: str
    organization_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo
