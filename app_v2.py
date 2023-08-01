import streamlit as st
import sqlite3
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms.openai import OpenAI
from langchain.memory import ConversationBufferMemory


# App Title and Page Config
st.set_page_config(page_title='SQL Chatbot')
with st.sidebar:
    st.title('SQL Chatbot')
    st.write("Use me to help you explore your database!")
    
    # OpenAI Credentials
    if 'OPENAI_API_KEY' in st.secrets:
        st.success('API key already provided!')
        # replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        OPENAI_API_KEY = st.text_input('Enter OpenAI API key:', type='password')
        if not len(OPENAI_API_KEY) == 51:
            st.warning('Please enter your credentials!')
        else:
            st.success('Proceed to entering your prompt message!')

# Connect to the database. You can replace the string with whatever database you want the chatbot to use.
conn = sqlite3.connect('chatbot_database.db')


# Create the agent executor
db = SQLDatabase.from_uri("sqlite:///./chatbot_database.db")
toolkit = SQLDatabaseToolkit(db=db, llm=OpenAI(temperature=0))

memory = ConversationBufferMemory(memory_key="chat_history")

suffix = """Begin!"

Relevant pieces of previous conversation:
{chat_history}
(You do not need to use these pieces of information if not relevant)

Question: {input}
Thought: I should look at the tables in the database to see what I can query.  Then I should query the schema of the most relevant tables.
{agent_scratchpad}
"""

agent_executor = create_sql_agent(
    llm=OpenAI(temperature=0),
    toolkit=toolkit,
    verbose=True,
    suffix=suffix,
    input_variables= ['chat_history', 'input', 'agent_scratchpad'],
    agent_executor_kwargs={'memory':memory}
)

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
    # string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    # for dict_message in st.session_state.messages:
    #     if dict_message["role"] == "user":
    #         string_dialogue += "User: " + dict_message["content"] + "\\n\\n"
    #     else:
    #         string_dialogue += "Assistant: " + dict_message["content"] + "\\n\\n"
    memory.load_memory_variables({})
    output = agent_executor.run(prompt_input)
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