from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI


class LLM:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")

    def get_llm(self, tools: list[BaseTool] = []):
        if tools:
            return self.llm.bind_tools(tools)
        return self.llm
