import io

import streamlit as st
from database.s3 import S3Storage


@st.cache_resource
def get_s3():
    return S3Storage()


s3 = get_s3()

if "documents" not in st.session_state:
    st.session_state.documents = []
if "pending_documents" not in st.session_state:
    st.session_state.pending_documents = []
if "pending_deletions" not in st.session_state:
    st.session_state.pending_deletions = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "initial_load_done" not in st.session_state:
    st.session_state.initial_load_done = False

if not st.session_state.documents and not st.session_state.initial_load_done:
    s3_files = s3.get_all_files()
    st.session_state.documents = [
        {
            "name": file,
            "type": "pdf" if file.endswith(".pdf") else "txt",
            "content_type": "application/pdf"
            if file.endswith(".pdf")
            else "text/plain",
        }
        for file in s3_files
    ]
    st.session_state.pending_documents = st.session_state.documents.copy()
    st.session_state.initial_load_done = True

st.title("📄 Manage Documents")
st.markdown(
    "Upload text or PDF documents to add to your knowledge base. These documents will be processed and used by the chatbot to answer your questions."
)

uploaded_files = st.file_uploader(
    "Upload documents",
    type=["txt", "pdf"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}",
)


if uploaded_files:
    if st.button("Add Documents"):
        existing_names = {doc["name"] for doc in st.session_state.pending_documents}
        added_count = 0
        skipped_count = 0

        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.read()
            file_obj = io.BytesIO(file_bytes)

            new_doc = {
                "name": uploaded_file.name,
                "type": "pdf" if uploaded_file.name.endswith(".pdf") else "txt",
                "content_type": "application/pdf"
                if uploaded_file.name.endswith(".pdf")
                else "text/plain",
                "file_obj": file_obj,
            }

            if uploaded_file.name in existing_names:
                skipped_count += 1
            else:
                st.session_state.pending_documents.append(new_doc)
                added_count += 1

        if added_count > 0:
            st.success(f"Added {added_count} document(s) to the pending list.")
        if skipped_count > 0:
            st.warning(f"Skipped {skipped_count} document(s) that already exist.")

        st.session_state.uploader_key += 1
        st.rerun()

if st.button("Save Changes", type="primary"):
    current_names = {doc["name"] for doc in st.session_state.documents}
    pending_names = {doc["name"] for doc in st.session_state.pending_documents}
    removed_names = list(current_names - pending_names)

    # Show progress indicator
    with st.spinner("Processing documents and creating embeddings..."):
        added_files, removed_files = s3.update_documents(
            st.session_state.pending_documents
        )

    st.session_state.documents = st.session_state.pending_documents.copy()
    st.session_state.pending_deletions = []

    if added_files:
        st.success(f"Added files: {', '.join(added_files)}")
    if removed_files:
        st.success(f"Removed files: {', '.join(removed_files)}")

    st.rerun()

if (
    st.session_state.pending_documents != st.session_state.documents
    or st.session_state.pending_deletions
):
    st.warning("You have unsaved changes. Click 'Save Changes' to persist them.")

st.header("Your Documents")
if st.session_state.pending_documents:
    for idx, doc in enumerate(st.session_state.pending_documents):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{doc['name']}**")
        with col2:
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                try:
                    if "file_obj" in doc:
                        st.info("Download available after saving")
                    else:
                        file_content, content_type = s3.download_file(doc["name"])
                        st.download_button(
                            label="Download",
                            data=file_content,
                            file_name=doc["name"],
                            mime=content_type,
                            key=f"download_btn_{idx}",
                        )
                except Exception as e:
                    st.error(f"Error downloading file: {str(e)}")

            with col2_2:
                if st.button("Delete", key=f"delete_{idx}"):
                    if doc["name"] not in st.session_state.pending_deletions:
                        st.session_state.pending_deletions.append(doc["name"])
                        st.session_state.pending_documents.remove(doc)
                        st.rerun()
else:
    st.info("No documents uploaded yet. Upload your first document above!")
