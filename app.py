import streamlit as st
import requests
import pandas as pd

# API URL from Streamlit secrets
API_URL = st.secrets.get("API_URL", "https://rag-system-hnez.onrender.com")

# Page configuration
st.set_page_config(
    page_title="RAG Document Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 RAG Document Assistant")
st.markdown("*Upload documents and ask AI questions about them!*")
st.divider()

# ─────────────────────────────────────
# SECTION 1 - UPLOAD DOCUMENT
# ─────────────────────────────────────
st.header("📁 Upload Document")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["txt", "pdf"],
    help="Supports TXT and PDF files only"
)

if uploaded_file is not None:
    if st.button("Upload Document", type="primary", key="upload_btn"):
        with st.spinner("Uploading and processing..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "multipart/form-data"
                )
            }
            try:
                response = requests.post(
                    f"{API_URL}/uploadfile/",
                    files=files,
                    timeout=120
                )
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        st.error(f"Error: {data['error']}")
                    else:
                        st.success(
                            f"✅ File uploaded! "
                            f"ID: {data['file_id']} — "
                            f"Processing in background..."
                        )
                else:
                    st.error("Upload failed!")
            except requests.exceptions.Timeout:
                st.error("Request timed out. Render may be waking up — try again in 30 seconds.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.divider()

# ─────────────────────────────────────
# SECTION 2 - YOUR DOCUMENTS
# ─────────────────────────────────────
st.header("📄 Your Documents")

try:
    response = requests.get(f"{API_URL}/", timeout=30)
    if response.status_code == 200:
        data = response.json()
        files = data.get("files", [])
        if files:
            df = pd.DataFrame(files)
            df.columns = ["File ID", "Filename"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No documents uploaded yet!")
except:
    st.warning("Could not fetch documents. API may be waking up.")

st.divider()

# ─────────────────────────────────────
# SECTION 3 - ASK A QUESTION
# ─────────────────────────────────────
st.header("💬 Ask a Question")

col1, col2 = st.columns([1, 3])

with col1:
    file_id = st.number_input(
        "File ID",
        min_value=1,
        value=1,
        help="Enter the ID of the document"
    )

with col2:
    question = st.text_input(
        "Your Question",
        placeholder="e.g. What are Jayesh's skills?",
        help="Ask anything about your document!"
    )

if st.button("🤖 Ask AI", type="primary", key="ask_btn"):
    if not question or question.strip() == "":
        st.warning("Please enter a question!")
    else:
        with st.spinner("AI is thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask/",
                    json={
                        "question": question,
                        "file_id": int(file_id)
                    },
                    timeout=120
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Answer:")
                    st.markdown(f"**{data['answer']}**")
                    if data.get("context_used"):
                        with st.expander("📌 See context used by AI"):
                            st.text(data["context_used"])
                else:
                    st.error("Could not get answer!")
            except requests.exceptions.Timeout:
                st.error("Request timed out. Try again in 30 seconds.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.divider()
st.markdown("Built with ❤️ using FastAPI + OpenAI + PostgreSQL")
