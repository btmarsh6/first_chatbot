import streamlit as st
import sqlite3
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms.openai import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory


# App Title and Page Config
st.set_page_config(page_title='SQL Chatbot')
with st.sidebar:
    st.title('SQL Chatbot')
    st.write("Use me to help you explore your database!")
    
# OpenAI Credentials
if "openai_api_key" in st.secrets:
    openai_api_key = st.secrets.openai_api_key
else:
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Enter an OpenAI API Key to continue")
    st.stop()
    
    # if 'OPENAI_API_KEY' in st.secrets:
    #     st.success('API key already provided!')
    #     # replicate_api = st.secrets['REPLICATE_API_TOKEN']
    # else:
    #     OPENAI_API_KEY = st.text_input('Enter OpenAI API key:', type='password')
    #     if not len(OPENAI_API_KEY) == 51:
    #         st.warning('Please enter your credentials!')
    #     else:
    #         st.success('Proceed to entering your prompt message!')

# Connect to the database. You can replace the string with whatever database you want the chatbot to use.
conn = sqlite3.connect('chatbot_database.db')


# Create the agent executor
db = SQLDatabase.from_uri("sqlite:///./chatbot_database.db")
toolkit = SQLDatabaseToolkit(db=db, llm=OpenAI(temperature=0, openai_api_key=openai_api_key))
msgs = StreamlitChatMessageHistory(key="langchain_messages")
memory = ConversationBufferMemory(chat_memory=msgs)

suffix = """Begin!"

Relevant pieces of previous conversation:
{chat_history}
(You do not need to use these pieces of information if not relevant)

Question: {input}
Thought: I should look at the tables in the database to see what I can query.  Then, I should query the schema of the most relevant tables.
{agent_scratchpad}
"""

agent_executor = create_sql_agent(
    llm=OpenAI(temperature=0, openai_api_key=openai_api_key),
    toolkit=toolkit,
    verbose=True,
    suffix=suffix,
    input_variables=['chat_history', 'input', 'agent_scratchpad'],
    agent_executor_kwargs={'memory': memory}
)

# Opening message
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

view_messages = st.expander("View the message contents in session state")

# Render current messages from StreamlitChatMessageHistory
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

if prompt := st.chat_input():
    st.chat_message("human").write(prompt)
    response = agent_executor.run(prompt)
    st.chat_message("ai").write(response)

with view_messages:
    """
    Memory initialized with:
    ```python
    msgs = StreamlitChatMessageHistory(key="langchain_messages")
    memory = ConversationBufferMemory(chat_memory=msgs)
    ```

    Contents of `st.session_state.langchain_messages`:
    """
    view_messages.json(st.session_state.langchain_messages)

# # Store LLM generated responses
# if "langchain_messages" not in st.session_state.keys():
#     st.session_state.langchain_messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# # Display or clear chat messages
# for message in st.session_state.langchain_messages:
#     with st.chat_message(message["role"]):
#         st.write(message["content"])

def clear_chat_history():
    st.session_state.langchain_messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# # Function for generating response
# def generate_response(prompt_input):
#     output = agent_executor.run(prompt_input)
#     return output

# # User-provided prompt
# if prompt := st.chat_input():
#     st.session_state.langchain_messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.write(prompt)

# # Generate a new response if last message is not from assistant.
# if st.session_state.langchain_messages[-1]["role"] != "assistant":
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             response = generate_response(prompt)
#             placeholder = st.empty()
#             full_response = ''
#             for item in response:
#                 full_response += item
#                 placeholder.markdown(full_response)
#             placeholder.markdown(full_response)
#         message = {"role": "assistant", "content": full_response}
#         st.session_state.langchain_messages.append(message)