from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="运维问题或诊断任务",
    )


class AgentResponse(BaseModel):
    question: str
    answer: str
    tool_calls: list[dict[str, Any]]
    tool_call_count: int
    stopped_by_limit: bool = False


class RAGAgentRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="运维诊断问题",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="知识库检索片段数量",
    )


class RAGAgentSource(BaseModel):
    chunk_id: str
    document_id: int | None = None
    chunk_index: int | None = None
    content: str
    distance: float | None = None


class RAGAgentResponse(BaseModel):
    knowledge_base_id: int
    question: str
    answer: str
    retrieved_count: int
    sources: list[RAGAgentSource]
    tool_calls: list[dict[str, Any]]
    tool_call_count: int
    stopped_by_limit: bool = False

class AgentChatRequest(BaseModel):
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


class AgentChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    tool_calls: list[dict[str, Any]]
    tool_call_count: int
    stopped_by_limit: bool = False