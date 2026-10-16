import os

from dotenv import load_dotenv
from sqlmodel import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./produtos.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
