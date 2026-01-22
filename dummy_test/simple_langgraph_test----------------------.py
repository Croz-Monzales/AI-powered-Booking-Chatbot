from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import Field,BaseModel
from langgraph.graph import START,END,StateGraph
from langgraph.graph.message import add_messages,BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated,Literal,List
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableConfig

# loading the LLM
llm =  ChatOllama(
    model = "llama3.1:8b",
    temperature = 0
)

memory = MemorySaver()
# state this is going to control the flow of the graph
class State(TypedDict):
    messages : Annotated[list,add_messages]
    
graph_builder = StateGraph(State)

# node
# simple chatbot
def chatbot(state: State):
    return {"messages":[llm.invoke(state["messages"])]}
 

graph_builder.add_node("chatbot",chatbot)
graph_builder.add_edge(START,"chatbot")
graph_builder.add_edge("chatbot",END)

graph = graph_builder.compile(checkpointer=memory)
config = RunnableConfig({"configurable":{"thread_id":"1"}})

user_input = None
while user_input != "c":
    user_input = input("Enter a message: ")
    if user_input == "c":
        print("okay breaking !")
        break

    output = graph.invoke({
        "messages":[{"role":"user","content":user_input}]},
        config = config)
    print(output["messages"][-1].content) 
    print("**********")
    print("all messages:",output["messages"])
