# database.py

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{os.getenv("DB_USER", "postgres")}:"
    f"{os.getenv("DB_PASSWORD", "admin")}@"
    f"{os.getenv("DB_HOST", "localhost")}:"
    f"{os.getenv('DB_PORT', '5532')}/"
    f"{os.getenv("DB_NAME", "postgres")}"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=2,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)