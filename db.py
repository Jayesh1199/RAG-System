# Write your code here
import os
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv

load_dotenv()

# Step 1 - Build database URL from .env
DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

# Step 2 - Create engine
engine = create_engine(DB_URL)

# Step 3 - Create session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Step 4 - Base for models
Base = declarative_base()

# Step 5 - Define tables
class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, unique=True, index=True)
    file_content = Column(Text)

class FileChunk(Base):
    __tablename__ = "file_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, index=True)
    chunk_text = Column(Text)
    chunk_embedding = Column(Vector(1536))

# Step 6 - Create tables + enable vector extension
def init_db():
    with engine.connect() as conn:
        conn.execute(
            __import__('sqlalchemy').text(
                "CREATE EXTENSION IF NOT EXISTS vector"
            )
        )
        conn.commit()
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

# Step 7 - Test connection
if __name__ == "__main__":
    try:
        init_db()
        session = SessionLocal()
        print("Database connected successfully!")
        session.close()
    except Exception as e:
        print(f"Database error: {e}")