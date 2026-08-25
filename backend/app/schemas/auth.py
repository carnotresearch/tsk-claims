from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserMeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    full_name: str | None
    role: str
    hospital_id: int | None
    is_active: bool
