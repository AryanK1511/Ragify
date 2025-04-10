from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.graph.node import Node
from agent.graph.state import AgentState
from agent.graph.tools import Tools


class AgentGraph:
    def __init__(self):
        self.react_graph = None
        self.builder = StateGraph(AgentState)
        self.memory_saver = MemorySaver()

    def build_graph(self, all_tools: list[BaseTool]):
        assistant_node = Node.create_assistant_node(all_tools)
        rag_node = Node.create_rag_node()

        self.builder.add_node("tools_node", ToolNode(all_tools))
        self.builder.add_node("assistant_node", assistant_node)
        # self.builder.add_node("rag_node", rag_node)

        # self.builder.add_edge(START, "rag_node")

        # self.builder.add_edge("rag_node", "assistant_node")

        self.builder.add_edge(START, "assistant_node")

        self.builder.add_conditional_edges(
            "assistant_node",
            tools_condition,
            {"tools": "tools_node", "end": END},
        )

        self.builder.add_edge("tools_node", "assistant_node")

        self.react_graph = self.builder.compile(checkpointer=self.memory_saver)

    def get_graph(self):
        self.build_graph(Tools().get_tools())
        return self.react_graph
