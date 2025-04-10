from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate


class AIUtils:
    @staticmethod
    def fetch_prompt():
        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content="You are a helpful assistant that can answer questions and help with tasks. Here is the additional context: {additional_context}"
                ),
                ("human", "{user_prompt}"),
            ]
        )
