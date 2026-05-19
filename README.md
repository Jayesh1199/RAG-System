# 🤖 RAG System - AI Document Assistant

A production-ready **Retrieval-Augmented Generation (RAG)** 
system that allows you to upload documents and ask 
AI-powered questions about them.

## 🚀 Features
- 📁 Upload TXT and PDF documents
- 🔍 OCR support for scanned PDFs
- 🧠 AI-powered question answering
- 💾 PostgreSQL vector database storage
- ⚡ Fast async processing with FastAPI
- 🔄 Background task processing

## 🛠️ Tech Stack
| Technology | Purpose |
|------------|---------|
| FastAPI | Backend API framework |
| OpenAI GPT | AI question answering |
| PostgreSQL | Database storage |
| pgvector | Vector embeddings |
| NLTK | Text processing |
| pytesseract | OCR for scanned PDFs |

## 📋 How It Works
```
Upload Document → Parse Text → Create Embeddings
        ↓
Ask Question → Find Similar Chunks → AI Answer!
```

## 🔧 Installation
```bash
# Clone the repository
git clone https://github.com/Jayesh1199/RAG-System.git

# Install dependencies
pip install fastapi openai sqlalchemy psycopg2-binary
pip install python-dotenv pgvector nltk pytesseract
pip install PyPDF2 pymupdf pillow python-multipart

# Set up environment variables
cp .env.example .env
# Add your OpenAI API key to .env

# Start PostgreSQL and run
uvicorn main:app --reload
```

## 📌 API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| / | GET | List all files |
| /uploadfile/ | POST | Upload document |
| /ask/ | POST | Ask AI question |
| /find-similar-chunks/{id} | GET | Find similar text |

## 💡 Usage
```bash
# Upload a document
curl -X POST 'http://localhost:8000/uploadfile/' \
  -F 'file=@document.txt'

# Ask a question
curl -X POST 'http://localhost:8000/ask/' \
  -H 'Content-Type: application/json' \
  -d '{"question": "Your question?", "file_id": 1}'
```

## 🔮 Future Features
- [ ] Streamlit UI frontend
- [ ] Multi-language support
- [ ] User authentication
- [ ] Support more file formats
- [ ] Chat history

## 👨‍💻 Author
**Jayesh Mohan**
