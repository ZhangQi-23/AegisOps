from fastapi import FastAPI

from app.database import Base, engine
from app.models import user
from app.models import knowledge_base as knowledge_base_model
from app.models import document_chunk

from app.api.auth import router as auth_router
from app.api.knowledge_base import router as knowledge_base_router
from app.api.document import router as document_router

from app.models import document
from app.api.qa import router as qa_router

from app.api.agent import router as agent_router

# 创建数据库表
Base.metadata.create_all(bind=engine)


app = FastAPI(
    swagger_ui_parameters={
        "persistAuthorization": True
    }
)


# 注册认证相关 API
app.include_router(auth_router)
app.include_router(knowledge_base_router)
app.include_router(document_router)
app.include_router(qa_router)
app.include_router(agent_router)

@app.get("/")
def root():
    return {
        "message": "AegisOps Backend Running"
    }