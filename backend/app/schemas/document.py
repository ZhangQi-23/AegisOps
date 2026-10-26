from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    knowledge_base_id: int
    original_filename: str
    file_type: str
    status: str
    error_message: str | None
    created_at: datetime
