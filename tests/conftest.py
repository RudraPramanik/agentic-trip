import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://at:at@localhost:5432/at",
)
