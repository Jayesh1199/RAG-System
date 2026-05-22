import streamlit as st
import requests
import time
import os
# Our FastAPI URL

API_URL = st.secrets.get("API_URL", "https://rag-system-hnez.onrender.com")

# Page configuration
# Sets title, icon and layout of the page
st.set_page_config(
    page_title="RAG Document Assistant",
    page_icon="🤖",
    layout="wide"
)

# Main title
# This shows at the top of the page
st.title("🤖 RAG Document Assistant")
st.markdown("*Upload documents and ask AI questions about them!*")

# Divider line
st.divider()

# ─────────────────────────────────────
# SECTION 1 - UPLOAD DOCUMENT
# ─────────────────────────────────────
# st.header → shows a section title
# st.file_uploader → shows upload button
# accepts only txt and pdf files

st.header("📁 Upload Document")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["txt", "pdf"],
    help="Supports TXT and PDF files only"
)

# When user clicks Upload button
if uploaded_file is not None:
    if st.button("Upload Document", type="primary"):
        
        # Show loading spinner while uploading
        with st.spinner("Uploading and processing..."):
            
            # Send file to FastAPI
            # requests.post = sends POST request
            # files = the file we're sending
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "multipart/form-data"
                )
            }
            response = requests.post(
            f"{API_URL}/ask/",
            json={
                "question": question,
                "file_id": int(file_id)
                },
             timeout=120
)
            
            # Check if upload worked
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    # Show red error message
                    st.error(f"Error: {data['error']}")
                else:
                    # Show green success message
                    st.success(
                        f"✅ File uploaded! "
                        f"ID: {data['file_id']} "
                        f"Processing in background..."
                    )
            else:
                st.error("Upload failed!")

st.divider()

# ─────────────────────────────────────
# SECTION 2 - YOUR DOCUMENTS
# ─────────────────────────────────────
# Calls FastAPI root endpoint
# Gets list of all uploaded files
# Shows them in a nice table

st.header("📄 Your Documents")

# Fetch documents from FastAPI
try:
    response = requests.get(f"{API_URL}/")
    if response.status_code == 200:
        data = response.json()
        files = data.get("files", [])
        
        if files:
            # Show files in a table
            # st.dataframe = shows nice table
            import pandas as pd
            df = pd.DataFrame(files)
            df.columns = ["File ID", "Filename"]
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        else:
            # Show info message if no files
            st.info("No documents uploaded yet!")
except:
    st.warning("Could not fetch documents!")

st.divider()

# ─────────────────────────────────────
# SECTION 3 - ASK A QUESTION
# ─────────────────────────────────────
# Shows dropdown to select document
# Shows text input for question
# Shows Ask AI button
# Shows answer from OpenAI

st.header("💬 Ask a Question")

# Two columns side by side
# col1 = file selector (narrow)
# col2 = question input (wide)
col1, col2 = st.columns([1, 3])

with col1:
    # Number input for file ID
    # user enters which file to ask about
    file_id = st.number_input(
        "File ID",
        min_value=1,
        value=1,
        help="Enter the ID of the document"
    )

with col2:
    # Text input for question
    question = st.text_input(
        "Your Question",
        placeholder="e.g. When was Obama president?",
        help="Ask anything about your document!"
    )

# Ask AI button
if st.button("🤖 Ask AI", type="primary"):
    
    # Check if question is empty
    if not question:
        st.warning("Please enter a question!")
    else:
        # Show loading spinner
        with st.spinner("AI is thinking..."):
            
            # Send question to FastAPI
            # json = sends as JSON data
            response = requests.post(
                f"{API_URL}/ask/",
                json={
                    "question": question,
                    "file_id": int(file_id)
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Show AI answer in green box
                st.success("✅ Answer:")
                st.markdown(
                    f"**{data['answer']}**"
                )
                
                # Show context used
                # This shows WHICH part of document
                # the AI used to answer!
                if data.get("context_used"):
                    with st.expander(
                        "📌 See context used by AI"
                    ):
                        st.text(data["context_used"])
            else:
                st.error("Could not get answer!")

st.divider()

# Footer
st.markdown(
    "Built with ❤️ using FastAPI + OpenAI + PostgreSQL"
)
