from typing import Dict, Generator, List

from config import settings
from database.qdrant import QdrantDatabase
from langchain.callbacks.tracers.langchain import LangChainTracer
from langchain_openai import ChatOpenAI
from utils.ai_utils import AIUtils
from utils.logger import logger


class AIService:
    def __init__(self):
        self.tracer = LangChainTracer()
        self.qdrant_db = QdrantDatabase()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
            callbacks=[self.tracer],
        )

    def generate_response(
        self, user_prompt: str, chat_history: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        try:
            logger.info(f"Fetching response for user prompt: {user_prompt}")
            prompt = AIUtils.fetch_prompt(chat_history)
            chain = prompt | self.llm
            additional_context = self.qdrant_db.search(user_prompt)

            for chunk in chain.stream(
                {
                    "user_prompt": user_prompt,
                    "additional_context": additional_context,
                }
            ):
                yield str(chunk.content) if hasattr(chunk, "content") else str(chunk)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield "An error occurred while generating the response."
