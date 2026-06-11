import streamlit as st
import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_URL = st.secrets["API_URL"]
API_KEY = st.secrets["API_KEY"]

AUTH_HEADERS = {"X-API-Key": API_KEY}

REQUEST_TIMEOUT_SHORT = 30
REQUEST_TIMEOUT_LONG  = 120

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RAG Document Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 RAG Document Assistant")
st.markdown("*Upload documents and ask AI questions about them.*")
st.divider()


# ---------------------------------------------------------------------------
# Section 1 — Upload Document
# ---------------------------------------------------------------------------
st.header("📁 Upload Document")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["txt", "pdf"],
    help="Supports TXT and PDF files only"
)

if uploaded_file is not None:
    if st.button("Upload Document", type="primary", key="upload_btn"):
        with st.spinner("Uploading and processing..."):

            mime_type = (
                "application/pdf"
                if uploaded_file.name.lower().endswith(".pdf")
                else "text/plain"
            )

            files = {
                "file": (uploaded_file.name, uploaded_file.getvalue(), mime_type)
            }

            try:
                response = requests.post(
                    f"{API_URL}/uploadfile/",
                    files=files,
                    headers=AUTH_HEADERS,
                    timeout=REQUEST_TIMEOUT_LONG
                )

                if response.status_code == 201:
                    file_id = response.json().get("file_id")
                    st.success(f"✅ Uploaded successfully — File ID: {file_id}")
                    st.cache_data.clear()

                elif response.status_code == 409:
                    st.warning("⚠️ This file already exists in the database.")
                elif response.status_code == 403:
                    st.error("🔒 Authentication failed — check your API key in secrets.")
                else:
                    st.error(f"Upload failed. Status {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                st.error("⏱ Request timed out. Render may be waking up — wait 30s and retry.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Could not reach the backend. Check that the API_URL is correct.")

st.divider()


# ---------------------------------------------------------------------------
# Section 2 — Document List
# ---------------------------------------------------------------------------
st.header("📄 Your Documents")

@st.cache_data(ttl=60, show_spinner=False)
def fetch_document_list() -> list[dict]:
    try:
        response = requests.get(
            f"{API_URL}/",
            headers=AUTH_HEADERS,
            timeout=REQUEST_TIMEOUT_SHORT
        )
        response.raise_for_status()
        return response.json().get("files", [])

    except requests.exceptions.RequestException as exc:
        st.warning(f"Could not fetch documents: {exc}")
        return []


documents = fetch_document_list()

if documents:
    df = pd.DataFrame(documents).rename(columns={"id": "File ID", "filename": "Filename"})
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No documents uploaded yet.")

st.divider()


# ---------------------------------------------------------------------------
# Section 3 — Ask a Question
# ---------------------------------------------------------------------------
st.header("💬 Ask a Question")
st.caption("💡 Try: 'What are Jayesh's technical skills?' using File ID 10")

col1, col2 = st.columns([1, 3])

with col1:
    file_id = st.number_input(
        "File ID",
        min_value=1,
        value=10,
        step=1,
        help="Enter the ID shown in the document list above"
    )

with col2:
    question = st.text_input(
        "Your Question",
        value="What are Jayesh's technical skills?",
        help="Ask anything about the selected document."
    )

if st.button("🤖 Ask AI", type="primary", key="ask_btn"):

    cleaned_question = question.strip()

    if not cleaned_question:
        st.warning("Please enter a question before submitting.")
    else:
        with st.spinner("Querying AI..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask/",
                    json={"question": cleaned_question, "file_id": int(file_id)},
                    headers=AUTH_HEADERS,
                    timeout=REQUEST_TIMEOUT_LONG
                )

                if response.status_code == 200:
                    payload = response.json()
                    st.success("✅ Answer:")
                    st.markdown(f"**{payload['answer']}**")

                    context = payload.get("context_used")
                    if context:
                        with st.expander("📌 Retrieved context used by AI"):
                            st.text(context)

                elif response.status_code == 403:
                    st.error("🔒 Authentication failed — check your API key.")
                elif response.status_code == 404:
                    st.error(f"File ID {file_id} not found. Upload the document first.")
                else:
                    st.error(
                        f"Request failed. Status {response.status_code}: {response.text}"
                    )

            except requests.exceptions.Timeout:
                st.error("⏱ Request timed out. Try again in 30 seconds.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Backend unreachable. Verify your API_URL in secrets.")

st.divider()
st.markdown("Built with FastAPI · OpenAI · PostgreSQL · pgvector")
