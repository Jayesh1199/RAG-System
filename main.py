from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, BackgroundTasks, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from db import SessionLocal, File, FileChunk, init_db
from file_parser import FileParser
from background_tasks import DocumentProcessor
import tempfile
import shutil

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API Key Authentication
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("API_KEY", "dev-key-change-in-production")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    """Validate API key on every protected endpoint."""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key"
        )
    return api_key

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="RAG System API",
    description="Production RAG pipeline with FastAPI + pgvector + OpenAI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — only allow Streamlit domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jayesh-rag-system.streamlit.app",
        "http://localhost:8501",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

class AskModel(BaseModel):
    question: str
    file_id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Health check — verifies DB connection too
# ---------------------------------------------------------------------------
@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Render pings this to confirm service and DB are both alive."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {str(e)}"
        )

# ---------------------------------------------------------------------------
# Root — list all files
# ---------------------------------------------------------------------------
@app.get("/")
def root(db: Session = Depends(get_db)):
    files = db.query(File).all()
    return {
        "message": "RAG System is live!",
        "files": [{"id": f.id, "filename": f.file_name} for f in files]
    }

# ---------------------------------------------------------------------------
# Upload — store file content in DB, not on disk
# ---------------------------------------------------------------------------
@app.post("/uploadfile/", status_code=201)
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Security(verify_api_key)
):
    # Validate file type
    allowed_types = [".txt", ".pdf"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=422,
            detail="Only .txt and .pdf files allowed"
        )

    # Read file bytes into memory
    file_bytes = await file.read()

    # Parse content using a temp file — avoids permanent disk storage
    # Temp files are automatically cleaned up after the with block
    try:
        with tempfile.NamedTemporaryFile(
            delete=True,
            suffix=file_ext
        ) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            parser = FileParser(filepath=tmp.name)
            content = parser.parse()
    except Exception as e:
        logger.error(f"Error parsing file: {e}")
        raise HTTPException(
            status_code=500,
            detail="File could not be parsed"
        )

    # Check for duplicate filename
    existing = db.query(File).filter(
        File.file_name == file.filename
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"File '{file.filename}' already exists. Use a different name."
        )

    # Save to database — content stored in DB, not on disk
    try:
        db_file = File(
            file_name=file.filename,
            file_content=content
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
    except Exception as e:
        logger.error(f"DB error: {e}")
        raise HTTPException(
            status_code=500,
            detail="File could not be saved to database"
        )

    # Process embeddings in background
    processor = DocumentProcessor(db=db, file_id=db_file.id)
    background_tasks.add_task(processor.chunk_and_embed, content)

    return {
        "info": "File saved and processing started!",
        "filename": file.filename,
        "file_id": db_file.id,
        "content_length": len(content)
    }

# ---------------------------------------------------------------------------
# Ask — RAG query endpoint
# ---------------------------------------------------------------------------
@app.post("/ask/")
async def ask_question(
    body: AskModel,
    db: Session = Depends(get_db),
    api_key: str = Security(verify_api_key)
):
    if not body.question.strip():
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty"
        )

    # Verify file exists
    file_exists = db.query(File).filter(
        File.id == body.file_id
    ).first()
    if not file_exists:
        raise HTTPException(
            status_code=404,
            detail=f"File with ID {body.file_id} not found"
        )

    # Embed the question
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=body.question
    )
    query_embedding = response.data[0].embedding

    # Find relevant chunks via cosine similarity
    chunks = db.query(FileChunk).filter(
        FileChunk.file_id == body.file_id
    ).order_by(
        FileChunk.chunk_embedding.l2_distance(query_embedding)
    ).limit(3).all()

    if not chunks:
        return {
            "answer": "No content found for this document. It may still be processing.",
            "context_used": ""
        }

    context = "\n".join([c.chunk_text for c in chunks])

    # Ask GPT with grounded context
    ai_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Answer based ONLY on the context provided. If the answer isn't in the context, say 'I don't have enough information to answer this.'"
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {body.question}"
            }
        ],
        temperature=0.2,
        max_tokens=500
    )

    return {
        "answer": ai_response.choices[0].message.content,
        "context_used": context[:200]
    }

# ---------------------------------------------------------------------------
# Find similar chunks
# ---------------------------------------------------------------------------
@app.get("/find-similar-chunks/{file_id}")
def find_similar_chunks(
    file_id: int,
    query: str,
    db: Session = Depends(get_db),
    api_key: str = Security(verify_api_key)
):
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding

    chunks = db.query(FileChunk).filter(
        FileChunk.file_id == file_id
    ).order_by(
        FileChunk.chunk_embedding.l2_distance(query_embedding)
    ).limit(3).all()

    return {
        "similar_chunks": [
            {"chunk_text": c.chunk_text}
            for c in chunks
        ]
    }
