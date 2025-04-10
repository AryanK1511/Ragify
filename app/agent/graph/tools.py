from config import settings
from langchain_tavily import TavilySearch


class Tools:
    def __init__(self):
        self.tools = []

    def add_search_tool(self):
        web_search = TavilySearch(tavily_api_key=settings.TAVILY_API_KEY)
        self.tools.append(web_search)

    def get_tools(self):
        self.add_search_tool()
        return self.tools
