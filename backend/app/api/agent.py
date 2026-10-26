import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.langchain_agent_service import (
    run_agent_langchain,
)
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.knowledge_base_service import get_knowledge_base
from app.services.rag_agent_service import run_rag_agent
from app.schemas.agent import RAGAgentRequest, RAGAgentResponse

from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.chat_history_service import (
    add_message,
    get_history,
)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent",
    tags=["AI Agent"],
)


@router.post(
    "/knowledge-bases/{knowledge_base_id}/run",
    response_model=RAGAgentResponse,
)
def run_rag_agent_api(
    knowledge_base_id: int,
    request: RAGAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 校验知识库归属，避免跨用户访问
    knowledge_base = get_knowledge_base(
        db=db,
        knowledge_base_id=knowledge_base_id,
        owner_id=current_user.id,
    )

    if knowledge_base is None:
        raise HTTPException(
            status_code=404,
            detail="知识库不存在或无权访问",
        )

    # 2. 执行 RAG + Agent 联合诊断
    try:
        return run_rag_agent(
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
        logger.exception(
            "RAG + Agent 联合诊断失败，user_id=%s",
            current_user.id,
        )
        raise HTTPException(
            status_code=502,
            detail="联合诊断失败，请检查后端日志",
        ) from exc

@router.post(
    "/run",
    response_model=AgentResponse,
)
def run_agent_api(
    request: AgentRequest,
    current_user: User = Depends(get_current_user),
):
    # 保留数据库依赖，沿用项目现有的认证与依赖注入方式。
    # 当前 Redis 诊断工具只读取 Redis，不依赖用户数据库查询。

    try:
        result = run_agent_langchain(request.question)

        return {
            "question": result["question"],
            "answer": result["answer"],
            "tool_calls": result["tool_calls"],
            "tool_call_count": result["tool_call_count"],
            "stopped_by_limit": result.get(
                "stopped_by_limit",
                False,
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Agent 执行失败，user_id=%s",
            current_user.id,
        )
        raise HTTPException(
            status_code=502,
            detail="Agent 执行失败，请检查后端日志及 DeepSeek 服务状态",
        ) from exc


@router.post(
    "/chat",
    response_model=AgentChatResponse,
)
def agent_chat_api(
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
):
    # 1. 获取当前用户的会话历史
    history = get_history(
        user_id=current_user.id,
        session_id=request.session_id,
    )

    # 2. 调用 Agent，结合历史生成回答
    try:
        result = run_agent_langchain(
            question=request.question,
            history=history,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Agent 多轮对话执行失败，user_id=%s",
            current_user.id,
        )
        raise HTTPException(
            status_code=502,
            detail="Agent 对话暂时失败，请检查后端日志",
        ) from exc

    # 3. 保存本轮对话
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

    return {
        "session_id": request.session_id,
        "question": result["question"],
        "answer": result["answer"],
        "tool_calls": result["tool_calls"],
        "tool_call_count": result["tool_call_count"],
        "stopped_by_limit": result.get("stopped_by_limit", False),
    }
