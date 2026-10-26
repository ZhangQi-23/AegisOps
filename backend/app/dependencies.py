from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.models.user import User
from app.core.redis_client import redis_client
from app.core.security import SECRET_KEY, ALGORITHM


# Bearer Token 认证
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户

    流程：
    1. 从请求头获取 JWT
    2. 验证 JWT
    3. 检查 Redis 中是否存在该 Token
    4. 查询 MySQL 中的用户
    5. 返回当前用户
    """

    # 1. 获取 JWT Token
    token = credentials.credentials

    # 2. 解析并验证 JWT
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期"
        )

    # 3. 获取用户 ID
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少用户信息"
        )

    # 4. 检查 Redis 中是否存在 Token
    redis_key = f"login:token:{token}"
    stored_user_id = redis_client.get(redis_key)

    if stored_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录"
        )

    # 5. 查询 MySQL 用户
    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    # 6. 返回当前用户
    return user

def require_admin(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user