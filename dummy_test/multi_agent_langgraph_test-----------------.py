from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from pydantic import Field,BaseModel
from langgraph.graph import START,END,StateGraph
from langgraph.prebuilt import ToolNode 
from langgraph.graph.message import add_messages,BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated,Literal,List
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

# -----------------------------------------------------
# loading the LLM
llm =  ChatOllama(
    model = "llama3.1:8b",
    temperature = 0
)

class MessageType(BaseModel):
    message_type : Literal["logical","therapist"] = Field(
        description="""
        Classifies if the message is logical or emotional. If emotional, its therapist.
        If its logical then its logical.
        """)


# ------------------------------------------------------------
# STATE CONFIGS
memory = MemorySaver()
# state this is going to control the flow of the graph

class State(TypedDict):
    messages : Annotated[list,add_messages]
    message_type : str | None

# -------------------------------------------------------------------
# NODE FUNCTIONS

def classify(state: State):
    latest_message = state["messages"][-1]

    prompt = """
    you are an expert psychologist, you will be given a sentence/message  from a user.
    you need to correctly identify the tone of the user.
    if the person is talking in an emotional way, and needs emotional support, classify the message as 'therapist'.
    if the person is talking in a logical way and needs a logical answer, classify the message as 'logical'.
    If its related to math, you need to classify it as logical
    you are a crucial part of a bigger system that helps human civilization. So be responsible and 
    analyse carefully !
    Here is the message : {message}
    """
    prompt_template = ChatPromptTemplate.from_template(prompt)

    # call the chain
    classifier_llm = llm.with_structured_output(MessageType)
    chain = prompt_template | classifier_llm

    result = chain.invoke({"message": latest_message})
    return {"message_type": result.message_type}

# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
def route(state: State):
    # agent to route the call to the proper agent based on the message type
    message_type = state["message_type"]

    if message_type == "logical":
        # call the logical agent for appropriate response
        return {"next":"logical"}

    elif message_type == "therapist":
        # call the therapist agent for appropriate response
        return {"next":"therapist"}
    else:
        raise ValueError("The meesage type is not correct")

    pass
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------

def logical_agent(state:State):
    user_message = state["messages"][-1]

    prompt = """
    You are someone with a very clear mind and you always take the logical route to answer any question
    /message directed at you. You break what ever is said into logics, you say it out loud and
    then give your response and also say why your repsonse is logical.

    here is a message :{message}
    """
    prompt_template = ChatPromptTemplate.from_template(prompt)
    logical_agent_chain = prompt_template | llm | StrOutputParser()
    print("logical agent is invoked")
    return {"messages":logical_agent_chain.invoke(input={"message":user_message})}

# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
def therapist_agent(state:State):

    user_message = state["messages"][-1]

    prompt = """
    You are an expert therapist. You understand people very well and always talk to them the way a 
    therapist talks to the patient. Keep in mind that your responses will affect the user more as he/she
    is not in a good state right now. Be responsible and professional. You are the critical part of their lives
    right now. Good luck with handling them properly.
    here is a message :{message}
    """
    prompt_template = ChatPromptTemplate.from_template(prompt)
    therapist_agent_chain = prompt_template | llm | StrOutputParser()
    print("therapist agent invoked")
    return {"messages":therapist_agent_chain.invoke(input={"message":user_message})}

# ---------------------------------------------------------------------

# -----------------------------------------------------
# new control flow with custom tool node integrated

# defining the tool funciton
@tool 
def add(a,b):
    # performs the math operations
    return a+b

# converting that into a tool node
tool_node = ToolNode([add])

# tool node integrated with logical agent

# condition edge function
def add_tool_router(state:State):
    last_message = state["messages"][-1]

    if hasattr(last_message,"tool_calls"):
        if len(last_message["tool_calls"]) > 0:
            return "tool_node"
        else:
            return END
    else:
        return END

# new workflow of the whole langgraph

    # this function comes after the
# graph building
graph_builder = StateGraph(State)

# add nodes
graph_builder.add_node("classifier",classify)
graph_builder.add_node("router",route)
graph_builder.add_node("logical_agent_node",logical_agent)
graph_builder.add_node("tool_node",tool_node)
graph_builder.add_node("therapist_agent_node",therapist_agent)

# add edges
graph_builder.add_edge(START,"classifier")
graph_builder.add_edge("classifier","router")
graph_builder.add_conditional_edges(
    "router",
    lambda state: state["next"],path_map={"logical":"logical_agent_node","therapist":"therapist_agent_node"}
)

graph_builder.add_conditional_edges("logical_agent_node",add_tool_router)

graph_builder.add_edge("logical_agent_node",END)
graph_builder.add_edge("therapist_agent_node",END)

chatbot_graph = graph_builder.compile(checkpointer=memory)


# user interface
config = RunnableConfig({"configurable":{"thread_id":"1"}})
def chatbot():
    state = {"messages":[],"message_type":None}
    user_input = None
    # Initialize state if it doesn't exist
    if "messages" not in state:
        state = {"messages": []}
    while True:
        user_input = input("user: ")
        
        if user_input.lower() == "c":
            print("okay breaking!")
            break

        state = chatbot_graph.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config= config
        )

        # Access the last message from the updated state
        assistant_message = state["messages"][-1]
        print(f"Assistant: {assistant_message.content}")
 
chatbot()
