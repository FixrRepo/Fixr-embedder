# database.py

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{os.environ['DB_USER']}:"
    f"{os.environ['DB_PASSWORD']}@"
    f"{os.environ['DB_HOST']}:"
    f"{os.getenv('DB_PORT', '5432')}/"
    f"{os.environ['DB_NAME']}"
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