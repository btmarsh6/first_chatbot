import streamlit as st
import sqlite3
from langchain.agents import ZeroShotAgent, create_sql_agent, AgentExecutor
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms.openai import OpenAI
from langchain.chat_models.openai import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory
from langchain import SQLDatabaseChain


# App Title and Page Config
st.set_page_config(page_title='SQL Chatbot')
with st.sidebar:
    st.title('SQL Chatbot')
    st.write("Use me to help you explore your database!")

# Connect to the database. You can replace the string with whatever database you want the chatbot to use.
conn = sqlite3.connect('chatbot_database.db')


# Create the agent executor
db = SQLDatabase.from_uri("sqlite:///./chatbot_database.db")
toolkit = SQLDatabaseToolkit(db=db, llm=OpenAI(temperature=0))

prefix = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

If the question does not seem related to the database, just return "I don\'t know" as the answer.
"""
suffix = """Begin!"

Relevant pieces of previous conversation:
{history}
(You do not need to use these pieces of information if not relevant)

Question: {input}
Thought: I should look at the tables in the database to see what I can query.  Then I should query the schema of the most relevant tables.
{agent_scratchpad}
"""

prompt = ZeroShotAgent.create_prompt(
    tools=toolkit,
    prefix=prefix,
    suffix=suffix,
    input_variables=["input", "chat_history", "agent_scratchpad"],
)
memory = ConversationBufferMemory(memory_key="chat_history")
llm_chain = SQLDatabaseChain(llm=OpenAI(temperature=0), prompt=prompt)
agent = ZeroShotAgent(llm_chain=llm_chain, tools=toolkit, verbose=True)
agent_chain = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=toolkit, verbose=True, memory=memory
)
# agent_executor = create_sql_agent(
#     llm=OpenAI(temperature=0),
#     toolkit=toolkit,
#     verbose=True
# )
# memory = ConversationBufferMemory(memory_key = 'history' , input_key = 'input')
# llm = ChatOpenAI(model_name = 'gpt-3.5-turbo' , temperature = 0)
# suffix = """Begin!

# Relevant pieces of previous conversation:
# {history}
# (You do not need to use these pieces of information if not relevant)

# Question: {input}
# Thought: I should look at the tables in the database to see what I can query.  Then I should query the schema of the most relevant tables.
# {agent_scratchpad}
# """
# agent_executor = create_sql_agent(
#     llm = llm,
#     toolkit = SQLDatabaseToolkit(db=db, llm=llm),
#     agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#     input_variables = ["input", "agent_scratchpad","history"],
#     suffix = suffix, # must have history as variable,
#     agent_executor_kwargs = {'memory':memory}
# )


# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating response
def generate_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\\n\\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\\n\\n"
    output = agent_chain.run(prompt_input)
    return output

# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant.
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)