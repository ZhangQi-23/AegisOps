from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# 创建知识库时，客户端需要提交的数据
class KnowledgeBaseCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="知识库名称",
    )
    description: str | None = Field(
        default=None,
        description="知识库描述",
    )


# 更新知识库时，允许修改的字段
class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = None


# 返回给客户端的知识库信息
class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
