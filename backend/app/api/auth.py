from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import register_user, login_user

from app.dependencies import get_current_user,require_admin
from app.models.user import User

router = APIRouter(
    prefix="/api/auth",
    tags=["认证"]
)


# =========================
# 用户注册
# =========================

@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    user = register_user(
        db=db,
        username=request.username,
        password=request.password
    )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )

    return {
        "message": "注册成功",
        "user_id": user.id,
        "username": user.username
    }


# =========================
# 用户登录
# =========================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    result = login_user(
        db=db,
        username=request.username,
        password=request.password
    )

    # 用户不存在或者密码错误
    if result is None:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )

    return result

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }

@router.get("/admin/test")
def admin_test(
    current_user: User = Depends(require_admin)
):
    return {
        "message": "管理员权限验证成功",
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }