from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str | None = None
    role: str = "hospital_user"
    hospital_id: int | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("admin", "hospital_user"):
            raise ValueError("role must be 'admin' or 'hospital_user'")
        return v

    @field_validator("hospital_id")
    @classmethod
    def hospital_required_for_hospital_user(cls, v, info):
        role = info.data.get("role", "hospital_user")
        if role == "hospital_user" and v is None:
            raise ValueError("hospital_id is required for hospital_user role")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None
    hospital_id: int | None = None


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    full_name: str | None
    role: str
    hospital_id: int | None
    is_active: bool
