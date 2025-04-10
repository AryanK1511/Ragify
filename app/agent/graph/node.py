from database.qdrant import QdrantDatabase
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import MessagesState

from agent.graph.llm import LLM

sys_msg = SystemMessage(content="You are a helpful assistant.")


class Node:
    @staticmethod
    def create_assistant_node(all_tools: list[BaseTool]):
        def assistant_node(state: MessagesState):
            llm = LLM().get_llm(all_tools)
            return {"messages": [llm.invoke([sys_msg] + state["messages"])]}

        return assistant_node

    @staticmethod
    def create_rag_node():
        db = QdrantDatabase()

        def rag_function(state):
            messages = state["messages"]
            if not messages:
                return state

            last_message = messages[-1]
            query = last_message.content

            docs = db.search(query)

            context = _format_docs(docs)

            system_message = SystemMessage(
                content=f"Here is some relevant information from the database:\n\n{context}"
            )

            new_state = state.copy()
            new_state["messages"] = [system_message] + messages

            return new_state

        return rag_function


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(
        [f"Document {i+1}: {doc.page_content}" for i, doc in enumerate(docs)]
    )
