# app/chat.py


from external.streamlit import st
from services.ai_service import AIService

ai_service = AIService()


st.title("Simple chat")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_stream = ai_service.generate_response(prompt)
        response_text = st.write_stream((chunk.content for chunk in response_stream))
    st.session_state.messages.append({"role": "assistant", "content": response_text})
