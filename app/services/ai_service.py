from config import settings
from langchain_openai import ChatOpenAI


class AIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=settings.OPENAI_API_KEY
        )

    def generate_response(self, message: str) -> str:
        return self.llm.stream(message)
