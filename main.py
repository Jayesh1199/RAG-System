from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, BackgroundTasks, Depends
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import shutil
import logging
from db import SessionLocal, File, FileChunk, init_db
from file_parser import FileParser
from background_tasks import DocumentProcessor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DB on startup — not at import time
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
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

# Health check — Render pings this to confirm service is alive
@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def root(db: Session = Depends(get_db)):
    files = db.query(File).all()
    return {
        "message": "RAG System is live!",
        "files": [{"id": f.id, "filename": f.file_name} for f in files]
    }

@app.post("/uploadfile/")
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    allowed_types = [".txt", ".pdf"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        return {"error": "Only .txt and .pdf files allowed!"}

    folder = "sources"
    os.makedirs(folder, exist_ok=True)
    file_location = os.path.join(folder, file.filename)

    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return {"error": "File could not be saved!"}

    try:
        parser = FileParser(filepath=file_location)
        content = parser.parse()
    except Exception as e:
        logger.error(f"Error parsing file: {e}")
        return {"error": "File could not be parsed!"}

    try:
        db_file = File(file_name=file.filename, file_content=content)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return {"error": "File could not be saved to database!"}

    processor = DocumentProcessor(db=db, file_id=db_file.id)
    background_tasks.add_task(processor.chunk_and_embed, content)

    return {
        "info": "File saved and processing started!",
        "filename": file.filename,
        "file_id": db_file.id
    }

@app.get("/find-similar-chunks/{file_id}")
def find_similar_chunks(file_id: int, query: str, db: Session = Depends(get_db)):
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

    return {"similar_chunks": [{"chunk_text": c.chunk_text} for c in chunks]}

@app.post("/ask/")
async def ask_question(body: AskModel, db: Session = Depends(get_db)):
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=body.question
    )
    query_embedding = response.data[0].embedding

    chunks = db.query(FileChunk).filter(
        FileChunk.file_id == body.file_id
    ).order_by(
        FileChunk.chunk_embedding.l2_distance(query_embedding)
    ).limit(3).all()

    context = "\n".join([c.chunk_text for c in chunks])

    ai_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Answer based on this context:\n{context}"},
            {"role": "user", "content": body.question}
        ]
    )

    return {
        "answer": ai_response.choices[0].message.content,
        "context_used": context[:200]
    }
