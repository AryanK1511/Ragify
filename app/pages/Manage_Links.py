# app/pages/Manage_Links.py

import streamlit as st
from database.mongodb import MongoDB
from database.qdrant import QdrantDatabase
from utils.logger import logger
from utils.validation_utils import ValidationUtils


@st.cache_resource
def get_mongodb():
    return MongoDB()


@st.cache_resource
def get_qdrant():
    return QdrantDatabase()


db = get_mongodb()
qdrant_db = get_qdrant()

if "links" not in st.session_state:
    st.session_state.links = []
if "pending_links" not in st.session_state:
    st.session_state.pending_links = []
if "pending_deletions" not in st.session_state:
    st.session_state.pending_deletions = []
if "new_link" not in st.session_state:
    st.session_state.new_link = ""

st.title("🔗 Manage Links")
st.markdown(
    "The scraped content from the links that you add here will be added to the knowledge base for the chatbot which it will then leverage to answer your questions."
)


if not st.session_state.pending_links and not st.session_state.links:
    st.session_state.links = db.get_all_links()
    st.session_state.pending_links = st.session_state.links.copy()


with st.form("add_link_form"):
    if "reset_new_link" in st.session_state and st.session_state.reset_new_link:
        st.session_state.new_link = ""
        st.session_state.reset_new_link = False

    new_link = st.text_input(
        "Enter URL", placeholder="https://example.com", key="new_link"
    )
    submit_button = st.form_submit_button("Add Link")

    if submit_button:
        if not new_link or not ValidationUtils.is_url_valid(new_link):
            st.error("Please enter a valid URL.")
        elif new_link not in st.session_state.pending_links:
            st.session_state.pending_links.append(new_link)
            st.session_state.reset_new_link = True
            st.rerun()
        else:
            st.warning(f"Link already exists: {new_link}")

if st.button("Save Changes", type="primary"):
    try:
        db.sync_links(st.session_state.pending_links)
        new_links = [
            link
            for link in st.session_state.pending_links
            if link not in st.session_state.links
        ]
        removed_links = [
            link
            for link in st.session_state.links
            if link not in st.session_state.pending_links
        ]

        logger.info(f"New links: {new_links}")
        logger.info(f"Removed links: {removed_links}")

        with st.spinner("Processing links and creating embeddings..."):
            qdrant_db.sync_webpage_embeddings(new_links, removed_links)

        st.session_state.links = db.get_all_links()
        st.session_state.pending_links = st.session_state.links.copy()
        st.session_state.pending_deletions = []
        st.rerun()
    except Exception as e:
        st.error(f"Error saving changes: {str(e)}")

if (
    st.session_state.pending_links != st.session_state.links
    or st.session_state.pending_deletions
):
    st.warning("You have unsaved changes. Click 'Save Changes' to persist them.")

st.header("Your Links")
if st.session_state.pending_links:
    for idx, link in enumerate(st.session_state.pending_links):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"[{link}]({link})")
        with col2:
            if st.button("Delete", key=f"delete_{idx}"):
                if link not in st.session_state.pending_deletions:
                    st.session_state.pending_deletions.append(link)
                    st.session_state.pending_links.remove(link)
                    st.rerun()
else:
    st.info("No links added yet. Add your first link above!")
