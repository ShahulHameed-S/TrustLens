from pydantic import BaseModel
from uuid import UUID

class RoleBase(BaseModel):
    name: str

class RoleResponse(RoleBase):
    id: UUID

    class Config:
        from_attributes = True
