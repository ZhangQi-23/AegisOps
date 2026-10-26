from datetime import datetime, timedelta, timezone

import jwt


# JWT 密钥
SECRET_KEY = "aegisops-secret-key-change-this-later"

# JWT 加密算法
ALGORITHM = "HS256"

# Token 有效时间：2小时
ACCESS_TOKEN_EXPIRE_MINUTES = 120


def create_access_token(data: dict):
    """
    创建 JWT Token
    """

    # 复制一份数据，避免修改原数据
    to_encode = data.copy()

    # 设置过期时间
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    # 生成 JWT
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt