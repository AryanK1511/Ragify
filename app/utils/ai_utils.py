from typing import Dict, List

from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from utils.logger import logger


class AIUtils:
    @staticmethod
    def fetch_prompt(chat_history: List[Dict[str, str]]):
        formatted_chat_history = AIUtils.format_chat_history(chat_history)
        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content="""
                        You are a helpful, knowledgeable, and kind assistant. Your role is to answer user questions using the context retrieved from uploaded files and provided links.

                        Please follow these guidelines carefully:

                        1. **Always begin your response by listing the sources used** to answer the user's question. Use a clear and readable format (e.g., filenames, URLs, page numbers, etc.) before giving the actual answer.
                        2. Only use the provided context to answer the user's question. If the answer is not available in the context, respond politely and **do not** guess.
                        3. If the question requires real-time data or falls outside the scope of the context, use your available tools (e.g., web search) if permitted.
                        4. Be thorough yet concise — like a friendly, thoughtful teacher who wants the user to understand deeply.
                        5. If the user asks for clarification (e.g., "Explain this" or "What does this mean?"), provide an insightful and easy-to-understand explanation.
                        6. Always be respectful. Never respond with anything inappropriate, offensive, or irrelevant.
                    """.strip()
                ),
                *formatted_chat_history,
                (
                    "human",
                    "Here is the relevant context: {additional_context}\nHere is the user's current question: {user_prompt}",
                ),
            ]
        )

    @staticmethod
    def format_chat_history(
        chat_history: List[Dict[str, str]],
    ) -> List[HumanMessage | AIMessage]:
        message_history_messages = []
        for chat in chat_history:
            if chat["role"] == "human":
                message_history_messages.append(HumanMessage(content=chat["content"]))
            elif chat["role"] == "ai":
                message_history_messages.append(AIMessage(content=chat["content"]))
        logger.info(f"Message history messages: {message_history_messages}")
        return message_history_messages
