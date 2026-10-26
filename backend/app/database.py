import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base


# 读取 .env 文件
load_dotenv()


# 从环境变量中读取 MySQL 配置
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")


# MySQL 数据库连接地址
DATABASE_URL = (
    f"mysql+pymysql://"
    f"{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/"
    f"{MYSQL_DATABASE}"
)


# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    echo=True
)


# 创建数据库 Session
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False
)

# 创建 ORM 基类
Base = declarative_base()

# 获取数据库连接
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()