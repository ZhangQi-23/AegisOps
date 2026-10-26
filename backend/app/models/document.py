
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


class Document(Base):
    __tablename__ = "documents"

    # 文档的唯一 ID
    id = Column(Integer, primary_key=True, index=True)

    # 文档所属的知识库
    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id"),
        nullable=False,
        index=True,
    )

    # 用户上传时的原始文件名
    original_filename = Column(String(255), nullable=False)

    # 服务器实际保存的文件名或路径
    file_path = Column(String(500), nullable=False)

    # 文件类型，例如 txt、pdf、docx
    file_type = Column(String(20), nullable=False)

    # 文档处理状态：pending、processing、completed、failed
    status = Column(String(20), default="pending", nullable=False)

    # 文档处理失败时记录错误原因
    error_message = Column(Text, nullable=True)

    # 文档上传时间
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # 关联所属知识库
    knowledge_base = relationship("KnowledgeBase")
