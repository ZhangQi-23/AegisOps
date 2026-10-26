from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.qa import QARequest, QAResponse
from app.services.knowledge_base_service import get_knowledge_base
from app.services.rag_service import answer_question
from app.schemas.qa import QAChatRequest
from app.services.chat_history_service import (
    get_history,
    add_message,
)


router = APIRouter(
    prefix="/api/knowledge-bases",
    tags=["知识库问答"],
)


@router.post(
    "/{knowledge_base_id}/qa",
    response_model=QAResponse,
)
def knowledge_base_qa(
    knowledge_base_id: int,
    request: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 检查知识库是否存在，以及当前用户是否有权访问
    try:
        knowledge_base = get_knowledge_base(
            db=db,
            knowledge_base_id=knowledge_base_id,
            owner_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        # 不向客户端泄露数据库内部异常
        raise HTTPException(
            status_code=500,
            detail="检查知识库权限时发生错误",
        ) from exc

    if knowledge_base is None:
        raise HTTPException(
            status_code=404,
            detail="知识库不存在或无权访问",
        )

    # 2. 执行 RAG 检索与大模型回答
    try:
        result = answer_question(
            question=request.question,
            knowledge_base_id=knowledge_base_id,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        # 详细错误写在后端终端日志中，客户端只收到通用信息
        import logging

        logging.exception("知识库问答处理失败")
        raise HTTPException(
            status_code=502,
            detail="知识库问答暂时失败，请检查后端日志和模型服务配置",
        ) from exc

    # 3. 根据文档 ID 从 MySQL 查询来源文件名
    for source in result["sources"]:
        document = (
            db.query(Document)
            .filter(
                Document.id == source["document_id"],
                Document.knowledge_base_id == knowledge_base_id,
            )
            .first()
        )

        source["original_filename"] = (
            document.original_filename if document else None
        )

    # 4. 返回规范化的响应
    return {
        "knowledge_base_id": knowledge_base_id,
        "question": request.question,
        "answer": result["answer"],
        "retrieved_count": result["retrieved_count"],
        "sources": result["sources"],
    }


@router.post(
    "/{knowledge_base_id}/chat",
)
def knowledge_base_chat(
    knowledge_base_id: int,
    request: QAChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 检查知识库归属
    try:
        knowledge_base = get_knowledge_base(
            db=db,
            knowledge_base_id=knowledge_base_id,
            owner_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        import logging

        logging.exception("检查知识库权限失败")
        raise HTTPException(
            status_code=500,
            detail="检查知识库权限时发生错误",
        ) from exc

    if knowledge_base is None:
        raise HTTPException(
            status_code=404,
            detail="知识库不存在或无权访问",
        )

    # 2. 读取当前用户、当前会话的历史
    try:
        history = get_history(
            user_id=current_user.id,
            session_id=request.session_id,
        )
    except Exception as exc:
        import logging

        logging.exception("读取聊天历史失败")
        raise HTTPException(
            status_code=503,
            detail="读取会话历史失败，请检查 Redis",
        ) from exc

    # 3. 检索当前问题并生成回答
    try:
        result = answer_question(
            question=request.question,
            knowledge_base_id=knowledge_base_id,
            top_k=request.top_k,
            history=history,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        import logging

        logging.exception("RAG 多轮问答失败")
        raise HTTPException(
            status_code=502,
            detail="知识库问答暂时失败，请检查后端日志",
        ) from exc

    # 4. 查询来源文件名
    for source in result["sources"]:
        document = (
            db.query(Document)
            .filter(
                Document.id == source["document_id"],
                Document.knowledge_base_id == knowledge_base_id,
            )
            .first()
        )

        source["original_filename"] = (
            document.original_filename if document else None
        )

    # 5. 保存本轮对话
    try:
        add_message(
            user_id=current_user.id,
            session_id=request.session_id,
            role="user",
            content=request.question,
        )

        add_message(
            user_id=current_user.id,
            session_id=request.session_id,
            role="assistant",
            content=result["answer"],
        )
    except Exception as exc:
        import logging

        logging.exception("保存聊天历史失败")
        raise HTTPException(
            status_code=503,
            detail="回答已生成，但会话历史保存失败",
        ) from exc

    # 6. 返回答案、来源和会话 ID
    return {
        "knowledge_base_id": knowledge_base_id,
        "session_id": request.session_id,
        "question": request.question,
        "answer": result["answer"],
        "retrieved_count": result["retrieved_count"],
        "sources": result["sources"],
    }
