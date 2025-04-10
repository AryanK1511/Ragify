from config import settings
from langchain_openai import ChatOpenAI
from utils.ai_utils import AIUtils
from utils.logger import logger


class AIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=settings.OPENAI_API_KEY
        )

    def generate_response(self, user_prompt: str) -> str:
        try:
            chain = AIUtils.fetch_prompt() | self.llm
            additional_context = "You are a helpful assistant that can answer questions and help with tasks."
            return chain.stream(
                {"additional_context": additional_context, "user_prompt": user_prompt}
            )
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "An error occurred while generating the response."
