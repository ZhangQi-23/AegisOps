from pydantic import BaseModel, Field


class QARequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户提出的问题",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="最多检索多少个相关片段",
    )


class QASource(BaseModel):
    chunk_id: str
    document_id: int
    chunk_index: int
    content: str
    distance: float
    original_filename: str | None = None


class QAResponse(BaseModel):
    knowledge_base_id: int
    question: str
    answer: str
    retrieved_count: int
    sources: list[QASource]

class QAChatRequest(BaseModel):
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="聊天会话 ID",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="当前问题",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="检索片段数量",
    )