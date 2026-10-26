from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    # 知识库 ID
    id = Column(Integer, primary_key=True, index=True)

    # 所属用户 ID
    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # 知识库名称
    name = Column(String(100), nullable=False)

    # 知识库描述
    description = Column(Text, nullable=True)

    # 创建时间
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # 更新时间
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # 关联所属用户
    owner = relationship("User")
