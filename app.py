import requests
import streamlit as st


st.set_page_config(page_title="RAG Document Assistant", page_icon="📄", layout="wide")

API_URL = st.secrets["API_URL"].rstrip("/")
AUTH_HEADERS = {"X-API-Key": st.secrets["API_KEY"]}
REQUEST_TIMEOUT = 120


def reset_document():
    # A new selection must never keep using the previous document's ID or answer.
    st.session_state["active_file_id"] = None
    st.session_state["answer_payload"] = None
    st.session_state["answered_question"] = ""
    st.session_state["question"] = ""


for key, value in {
    "active_file_id": None,
    "answer_payload": None,
    "answered_question": "",
    "question": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.title("📄 RAG Document Assistant")
st.markdown("Upload a PDF or text file, then ask questions about its contents.")
st.divider()

st.header("1. Upload a document")
uploaded_file = st.file_uploader(
    "Choose a PDF or text file",
    type=["pdf", "txt"],
    key="document_upload",
    on_change=reset_document,
)

if uploaded_file is not None:
    if st.button(
        "Upload Document",
        type="primary",
        disabled=st.session_state["active_file_id"] is not None,
    ):
        with st.spinner("Uploading your document..."):
            mime_type = (
                "application/pdf"
                if uploaded_file.name.lower().endswith(".pdf")
                else "text/plain"
            )
            try:
                response = requests.post(
                    f"{API_URL}/uploadfile/",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), mime_type)},
                    headers=AUTH_HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                if response.status_code == 201:
                    file_id = response.json().get("file_id")
                    if type(file_id) is not int or file_id < 1:
                        raise ValueError("Invalid upload response")
                    st.session_state["active_file_id"] = file_id
                elif response.status_code == 409:
                    st.warning(
                        "This filename is already in use. Rename your file, "
                        "select it again, and upload it."
                    )
                elif response.status_code == 403:
                    st.error("The app could not authorize the upload. Please contact the app owner.")
                else:
                    st.error(f"Upload failed (status {response.status_code}). Please try again.")
            except requests.exceptions.Timeout:
                st.error("The upload timed out. The server may still have saved it. Please try again later.")
            except requests.exceptions.RequestException:
                st.error("Could not reach the server. Please try again shortly.")
            except ValueError:
                st.error("The server returned an unexpected response. Please contact the app owner.")

if st.session_state["active_file_id"] is not None:
    st.success("Document uploaded. Processing may take a moment before answers are available.")

st.divider()
st.header("2. Ask a question")
has_document = st.session_state["active_file_id"] is not None

if not has_document:
    st.info("Upload a document to start asking questions.")

question = st.text_input(
    "Your question",
    key="question",
    placeholder="For example: What are the key points in this document?",
    disabled=not has_document,
)

if st.button("Ask AI", type="primary", disabled=not has_document):
    st.session_state["answer_payload"] = None
    cleaned_question = question.strip()
    if not cleaned_question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Finding an answer in your document..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask/",
                    json={
                        "question": cleaned_question,
                        "file_id": st.session_state["active_file_id"],
                    },
                    headers=AUTH_HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                if response.status_code == 200:
                    payload = response.json()
                    if not isinstance(payload, dict) or not isinstance(payload.get("answer"), str):
                        raise ValueError("Invalid answer response")
                    st.session_state["answer_payload"] = payload
                    st.session_state["answered_question"] = cleaned_question
                elif response.status_code == 403:
                    st.error("The app could not authorize the question. Please contact the app owner.")
                elif response.status_code == 404:
                    st.error("This document is no longer available. Select and upload a document again.")
                    st.session_state["active_file_id"] = None
                else:
                    st.error(
                        f"The server could not answer your question (status {response.status_code}). "
                        "Please try again shortly. If this continues, contact the app owner."
                    )
            except requests.exceptions.Timeout:
                st.error("The answer took too long. Please try again shortly.")
            except requests.exceptions.RequestException:
                st.error("Could not reach the server. Please try again shortly.")
            except ValueError:
                st.error("The server returned an unexpected response. Please contact the app owner.")

payload = st.session_state["answer_payload"]
if payload is not None:
    st.subheader("Answer")
    st.caption("Question: " + st.session_state["answered_question"])
    st.markdown(payload["answer"])
    if payload.get("context_used"):
        with st.expander("View supporting text"):
            st.text(payload["context_used"])

st.divider()
st.caption("Built with FastAPI · OpenAI · PostgreSQL · pgvector")
