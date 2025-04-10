# app/chat.py

from external.streamlit import st
from services.ai_service import AIService

ai_service = AIService()

st.title("💬 Ragify Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.session_state.messages.append({"role": "human", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_stream = ai_service.generate_response(
            prompt, st.session_state.messages
        )
        response_text = st.write_stream(response_stream)

    st.session_state.messages.append({"role": "ai", "content": response_text})
