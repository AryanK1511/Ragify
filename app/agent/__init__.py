from constants import CHECKPOINTER_CONFIG
from langchain_core.messages import HumanMessage

from agent.graph import AgentGraph


class Agent:
    def __init__(self):
        self.graph = AgentGraph()
        self.agent = self.graph.get_graph()

    def query(self, message: str):
        if not self.agent:
            raise ValueError("Agent not initialized")

        result = self.agent.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=CHECKPOINTER_CONFIG,
        )

        assistant_message = result["messages"][-1]
        return assistant_message.content
