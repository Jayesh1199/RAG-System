# 🤖 RAG System - AI Document Assistant

A production-ready **Retrieval-Augmented Generation (RAG)** system that allows you to upload documents and ask AI-powered questions about them.

🌐 **Live Demo:** [jayesh-rag-system.streamlit.app](https://jayesh-rag-system.streamlit.app)

---

## 🚀 Features

- 📁 Upload TXT and PDF documents
- 🧠 AI-powered question answering grounded in your documents
- 🔍 Semantic vector search using pgvector
- ⚡ Fast async processing with FastAPI
- 🗄️ PostgreSQL vector database storage on Neon
- 📊 Background task processing with NLTK chunking

---

## 🏗️ Architecture

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| FastAPI | Backend API framework |
| OpenAI GPT-3.5 | AI question answering |
| OpenAI Embeddings | text-embedding-ada-002 |
| PostgreSQL + pgvector | Vector similarity search |
| Neon.tech | Serverless PostgreSQL hosting |
| NLTK | Sentence tokenization |
| PyPDF2 | PDF text extraction |
| Streamlit | Frontend UI |
| Render | FastAPI deployment |
| SQLAlchemy | ORM for database models |

---

## 📸 Screenshots

### Document Upload
![Upload](screenshots/upload.png)

### AI Answer
![Answer](screenshots/answer.png)

### Database (Neon pgvector)
![Database](screenshots/database.png)

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | List all uploaded files |
| `/uploadfile/` | POST | Upload and process document |
| `/ask/` | POST | Ask AI question |
| `/find-similar-chunks/{id}` | GET | Find similar text chunks |
| `/health` | GET | API health check |

---

## ⚙️ Local Setup

```bash
# Clone the repository
git clone https://github.com/Jayesh1199/RAG-System.git

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your DATABASE_URL and OPENAI_API_KEY

# Run the API
uvicorn main:app --reload
```

---

## 🌐 Deployment

| Service | Platform | URL |
|---|---|---|
| Frontend | Streamlit Cloud | jayesh-rag-system.streamlit.app |
| Backend API | Render | rag-system-hnez.onrender.com |
| Database | Neon PostgreSQL | neon.tech |

---

## 🔮 Future Features

- [ ] Multi-language support
- [ ] User authentication
- [ ] Chat history
- [ ] Support more file formats
- [ ] Streaming responses

---

## 👨‍💻 Author

**Jayesh Mohan**
