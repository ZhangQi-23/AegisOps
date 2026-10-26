from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk

from app.services.vector_store_service import (
    upsert_document_chunks,
)

def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    将文本切分成多个文本块。

    chunk_size：每个文本块的最大字符数
    overlap：相邻文本块之间重叠的字符数
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap 必须大于等于 0 且小于 chunk_size")

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks



def process_document(db: Session, document: Document) -> Document:
    document.status = "processing"
    document.error_message = None
    db.commit()

    try:
        if document.file_type.lower() != "txt":
            raise ValueError("当前仅支持 TXT 文档")

        file_path = Path(document.file_path)

        if not file_path.is_file():
            raise FileNotFoundError(
                f"文档文件不存在：{file_path}"
            )

        text = file_path.read_text(encoding="utf-8-sig")
        chunks = split_text(text)

        if not chunks:
            raise ValueError("文档内容为空，无法处理")

        # 1. 替换 MySQL 中原有的文本块
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).delete(synchronize_session=False)

        chunk_records = []

        for index, content in enumerate(chunks):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=content,
                )
            )

            chunk_records.append(
                {
                    "chunk_index": index,
                    "content": content,
                }
            )

        # 先提交文本块，让 MySQL 中的文本数据保存下来
        db.commit()

        # 2. 更新 Chroma 向量。
        # upsert_document_chunks 内部会在写入新向量后
        # 清理不再需要的旧向量。
        upsert_document_chunks(
            document_id=document.id,
            knowledge_base_id=document.knowledge_base_id,
            chunks=chunk_records,
        )

        # 3. 两步处理成功后，再标记为 completed
        document = db.query(Document).filter(
            Document.id == document.id
        ).first()

        document.status = "completed"
        document.error_message = None

        db.commit()
        db.refresh(document)

        return document

    except Exception as exc:
        db.rollback()

        document = db.query(Document).filter(
            Document.id == document.id
        ).first()

        if document is not None:
            document.status = "failed"
            document.error_message = str(exc)[:2000]
            db.commit()
            db.refresh(document)

        raise
