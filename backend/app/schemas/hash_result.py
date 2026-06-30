from pydantic import BaseModel, Field
from datetime import datetime

class HashResult(BaseModel):
    algorithm: str = Field(..., description="The hashing algorithm used, e.g., SHA-256")
    hash: str = Field(..., description="The calculated hexadecimal hash")
    size_bytes: int = Field(..., description="The size of the file in bytes")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the hash was generated")
