
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
)
from app.services.knowledge_base_service import (
    create_knowledge_base,
    get_knowledge_bases,
    get_knowledge_base,
    update_knowledge_base,
    delete_knowledge_base,
)


router = APIRouter(
    prefix="/api/knowledge-bases",
    tags=["知识库管理"],
)


@router.post(
    "",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_base_api(
    data: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_knowledge_base(
        db=db,
        owner_id=current_user.id,
        data=data,
    )


@router.get(
    "",
    response_model=list[KnowledgeBaseResponse],
)
def list_knowledge_bases_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_knowledge_bases(
        db=db,
        owner_id=current_user.id,
    )


@router.get(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
def get_knowledge_base_api(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = get_knowledge_base(
        db=db,
        knowledge_base_id=knowledge_base_id,
        owner_id=current_user.id,
    )

    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在或无权访问",
        )

    return knowledge_base


@router.patch(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
def update_knowledge_base_api(
    knowledge_base_id: int,
    data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = get_knowledge_base(
        db=db,
        knowledge_base_id=knowledge_base_id,
        owner_id=current_user.id,
    )

    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在或无权访问",
        )

    return update_knowledge_base(
        db=db,
        knowledge_base=knowledge_base,
        data=data,
    )


@router.delete(
    "/{knowledge_base_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_knowledge_base_api(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = get_knowledge_base(
        db=db,
        knowledge_base_id=knowledge_base_id,
        owner_id=current_user.id,
    )

    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在或无权访问",
        )

    delete_knowledge_base(
        db=db,
        knowledge_base=knowledge_base,
    )
