# Write your code here 
import nltk
import openai
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from db import FileChunk

load_dotenv()

# Download NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')

# Setup OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class DocumentProcessor:
    
    def __init__(self, db: Session, file_id: int):
        self.db = db
        self.file_id = file_id
    
    def chunk_and_embed(self, text: str):
        # Step 1 - Split text into sentences
        sentences = nltk.sent_tokenize(text)
        
        # Step 2 - Group sentences into chunks
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < 500:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Step 3 - Generate embeddings and save
        for chunk in chunks:
            embedding = self.get_embedding(chunk)
            
            db_chunk = FileChunk(
                file_id=self.file_id,
                chunk_text=chunk,
                chunk_embedding=embedding
            )
            self.db.add(db_chunk)
        
        self.db.commit()
        print(f"Saved {len(chunks)} chunks for file {self.file_id}")
    
    def get_embedding(self, text: str):
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding