# app/pages/Manage_Files.py

from database.qdrant import QdrantDatabase
from database.s3 import S3Storage
from external.streamlit import st
from utils.logger import logger

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "pending_documents" not in st.session_state:
    st.session_state.pending_documents = []
if "pending_deletions" not in st.session_state:
    st.session_state.pending_deletions = []
if "documents" not in st.session_state:
    st.session_state.documents = []


@st.cache_resource
def get_s3() -> S3Storage:
    return S3Storage()


@st.cache_resource
def get_qdrant() -> QdrantDatabase:
    return QdrantDatabase()


s3 = get_s3()
qdrant_db = get_qdrant()

if not st.session_state.documents:
    st.session_state.documents = s3.get_stored_filenames()

st.title("📝 Manage Files")
st.markdown(
    "Upload text or PDF documents to add to your knowledge base. These documents will be processed and used by the chatbot to answer your questions."
)

uploaded_files = st.file_uploader(
    "Upload documents",
    type=["txt", "pdf"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}",
)

existing_filenames = {doc for doc in st.session_state.documents}
pending_docs = []

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        content_type = uploaded_file.type

        if file_name in existing_filenames:
            st.warning(f"{file_name} already exists and will be overwritten.")

        pending_docs.append(
            {
                "file_obj": uploaded_file,
                "file_name": file_name,
                "content_type": content_type,
            }
        )

st.session_state.pending_documents = pending_docs

if st.button("Save Changes", type="primary"):
    uploaded_filenames, deleted_filenames = [], []

    for doc in st.session_state.pending_documents:
        try:
            s3.upload_files([doc])
            uploaded_filenames.append(doc["file_name"])
        except Exception as e:
            st.error(f"Error uploading {doc['file_name']}: {e}")
    st.session_state.pending_documents = []

    for filename in st.session_state.pending_deletions:
        try:
            s3.delete_files([filename])
            deleted_filenames.append(filename)
        except Exception as e:
            st.error(f"Error deleting {filename}: {e}")
    st.session_state.pending_deletions = []

    st.session_state.documents = s3.get_stored_filenames()

    logger.info(f"Uploaded files: {uploaded_filenames}")
    logger.info(f"Deleted files: {deleted_filenames}")

    try:
        with st.spinner("Processing documents and creating embeddings..."):
            qdrant_db.sync_document_embeddings(uploaded_filenames, deleted_filenames)
    except Exception as e:
        st.error(f"Error syncing document embeddings: {e}")

    st.session_state.uploader_key += 1
    st.rerun()

if st.session_state.pending_documents or st.session_state.pending_deletions:
    st.warning("You have unsaved changes. Click 'Save Changes' to persist them.")

st.header("Your Documents")
if st.session_state.documents:
    for idx, filename in enumerate(st.session_state.documents):
        if filename in st.session_state.pending_deletions:
            continue

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{filename}**")
        with col2:
            dl_col, del_col = st.columns(2)
            with dl_col:
                file_content, content_type = s3.download_file(filename)
                st.download_button(
                    label="Save",
                    data=file_content,
                    file_name=filename,
                    mime=content_type,
                    key=f"save_{idx}",
                )
            with del_col:
                if st.button("Delete", key=f"delete_{idx}", type="primary"):
                    if filename not in st.session_state.pending_deletions:
                        st.session_state.pending_deletions.append(filename)
                    st.rerun()
else:
    st.info("No documents uploaded yet. Upload your first document above!")
