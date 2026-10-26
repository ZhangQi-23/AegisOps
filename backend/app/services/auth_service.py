from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from app.models.user import User
from app.core.security import create_access_token
from app.core.redis_client import redis_client


# 创建密码哈希器
password_hash = PasswordHash.recommended()


def register_user(
    db: Session,
    username: str,
    password: str
):
    # 1. 查询用户名是否已经存在
    existing_user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing_user:
        return None

    # 2. 对密码进行加密
    hashed_password = password_hash.hash(password)

    # 3. 创建用户对象
    user = User(
        username=username,
        password_hash=hashed_password,
        role="user"
    )

    # 4. 保存到数据库
    db.add(user)
    db.commit()

    # 5. 刷新对象，获取数据库生成的 id
    db.refresh(user)

    return user


# =========================
# 用户登录
# =========================

def login_user(
    db: Session,
    username: str,
    password: str
):
    # 1. 根据用户名查询用户
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    # 用户不存在
    if not user:
        return None

    # 2. 验证密码
    if not password_hash.verify(
        password,
        user.password_hash
    ):
        return None

    # 3. 创建 JWT Token
    access_token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role
    })

    # 4. 将 Token 保存到 Redis
    # key：login:token:Token
    # value：用户ID
    # 过期时间：7200秒 = 2小时
    redis_client.set(
        f"login:token:{access_token}",
        str(user.id),
        ex=7200
    )

    # 5. 返回登录结果
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }