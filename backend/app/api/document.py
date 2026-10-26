from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.services.knowledge_base_service import get_knowledge_base

from app.models.document_chunk import DocumentChunk
from app.services.document_service import process_document

import logging
from app.services.cache_service import delete_knowledge_base_cache
from app.services.vector_store_service import delete_document_chunks

router = APIRouter(
    prefix="/api/knowledge-bases",
    tags=["文档管理"],
)

# 文件保存在 backend/uploads 目录
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

# 本阶段只允许上传 TXT，单个文件最大 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_SUFFIXES = {".txt"}


@router.post(
    "/{knowledge_base_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 检查知识库是否存在，以及当前用户是否拥有它
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

    # 2. 检查文件名和扩展名
    original_filename = Path(file.filename or "").name

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空",
        )

    suffix = Path(original_filename).suffix.lower()

    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目前只支持上传 TXT 文件",
        )

    # 3. 读取文件并限制大小
    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能上传空文件",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="文件大小不能超过 5 MB",
        )

    # 4. 使用随机文件名保存，避免重名和路径穿越
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    saved_filename = f"{uuid4().hex}{suffix}"
    file_path = UPLOAD_DIR / saved_filename

    try:
        file_path.write_bytes(content)

        # 5. 保存文档元数据到 MySQL
        document = Document(
            knowledge_base_id=knowledge_base.id,
            original_filename=original_filename,
            file_path=str(file_path.resolve()),
            file_type=suffix.lstrip("."),
            status="pending",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()

        # 如果数据库保存失败，清理刚刚写入的文件
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文档保存失败，请稍后重试",
        )

    finally:
        await file.close()


@router.post(
    "/{knowledge_base_id}/documents/{document_id}/process",
    response_model=DocumentResponse,
)
def process_document_api(
    knowledge_base_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 确认当前用户拥有这个知识库
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

    # 确认文档确实属于这个知识库
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.knowledge_base_id == knowledge_base.id,
    ).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )


    try:
        # 1. 先执行原有文档处理：解析、切分、向量化等
        processed_document = process_document(
            db=db,
            document=document,
        )

    except Exception as exc:
        logging.exception(
            "文档处理失败：knowledge_base_id=%s, document_id=%s",
            knowledge_base_id,
            document_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文档处理失败，请检查后端日志和文档状态",
        ) from exc

    # 2. 文档处理成功后，清除该知识库的 RAG 答案缓存
    try:
        deleted_count = delete_knowledge_base_cache(
            knowledge_base_id=knowledge_base_id,
        )

        logging.info(
            "文档处理成功，已清理知识库 RAG 缓存："
            "knowledge_base_id=%s, deleted_count=%s",
            knowledge_base_id,
            deleted_count,
        )

    except Exception:
        # 缓存清理失败不应让已完成的文档处理被误报为失败
        logging.exception(
            "清理 RAG 缓存失败：knowledge_base_id=%s",
            knowledge_base_id,
        )

    # 3. 返回原有文档处理结果
    return processed_document


@router.delete(
    "/{knowledge_base_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document_api(
    knowledge_base_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 检查知识库权限
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

    # 2. 确认文档属于指定知识库
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.knowledge_base_id == knowledge_base.id,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或无权访问",
        )

    # 提前保存文件路径，后续删除数据库记录后仍可使用
    file_path = Path(document.file_path)

    # 3. 先删除 Chroma 中该文档的向量
    # 如果这一步失败，就不继续删除 MySQL 记录
    try:
        delete_document_chunks(document_id)

    except Exception as exc:
        logging.exception(
            "删除 Chroma 文档向量失败：document_id=%s",
            document_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除文档向量失败，请检查后端日志",
        ) from exc

    # 4. 删除 MySQL 中的文本块和文档记录
    try:
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete(synchronize_session=False)

        db.delete(document)
        db.commit()

    except Exception as exc:
        db.rollback()

        logging.exception(
            "删除 MySQL 文档记录失败：document_id=%s",
            document_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除文档数据库记录失败，请检查后端日志",
        ) from exc

    # 5. 删除原始上传文件
    # 数据库记录已删除，文件清理失败时记录日志并继续
    try:
        file_path.unlink(missing_ok=True)

    except OSError:
        logging.exception(
            "删除原始文档文件失败：document_id=%s",
            document_id,
        )

    # 6. 清理这个知识库的 RAG 答案缓存
    try:
        deleted_count = delete_knowledge_base_cache(
            knowledge_base_id=knowledge_base_id,
        )

        logging.info(
            "文档删除完成，RAG 缓存已清理："
            "knowledge_base_id=%s, deleted_count=%s",
            knowledge_base_id,
            deleted_count,
        )

    except Exception:
        # 缓存清理失败不能撤销已经完成的文档删除
        logging.exception(
            "清理 RAG 缓存失败：knowledge_base_id=%s",
            knowledge_base_id,
        )

    # HTTP 204 不返回响应体
    return None
