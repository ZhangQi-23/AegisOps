
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
)


def create_knowledge_base(
    db: Session,
    owner_id: int,
    data: KnowledgeBaseCreate,
):
    """创建知识库"""
    knowledge_base = KnowledgeBase(
        owner_id=owner_id,
        name=data.name,
        description=data.description,
    )

    db.add(knowledge_base)
    db.commit()
    db.refresh(knowledge_base)

    return knowledge_base


def get_knowledge_bases(
    db: Session,
    owner_id: int,
):
    """查询当前用户的所有知识库"""
    return (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.owner_id == owner_id)
        .order_by(KnowledgeBase.created_at.desc())
        .all()
    )


def get_knowledge_base(
    db: Session,
    knowledge_base_id: int,
    owner_id: int,
):
    """查询当前用户的指定知识库"""
    return (
        db.query(KnowledgeBase)
        .filter(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.owner_id == owner_id,
        )
        .first()
    )


def update_knowledge_base(
    db: Session,
    knowledge_base: KnowledgeBase,
    data: KnowledgeBaseUpdate,
):
    """更新知识库"""
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(knowledge_base, field, value)

    db.commit()
    db.refresh(knowledge_base)

    return knowledge_base


def delete_knowledge_base(
    db: Session,
    knowledge_base: KnowledgeBase,
):
    """删除知识库"""
    db.delete(knowledge_base)
    db.commit()

    return True
