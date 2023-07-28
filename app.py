import streamlit as st
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms.openai import OpenAI

openai_api_key = st.secrets["OPENAI_KEY"]

# Connect to the database and execute the SQL script
conn = sqlite3.connect('chatbot_database.db')
with open('./Chinook_Sqlite.sql', 'r',encoding='cp1252', errors='replace') as f:
    sql_script = f.read()
conn.executescript(sql_script)
conn.close()

# Create the agent executor
db = SQLDatabase.from_uri("sqlite:///./chatbot_database.db")
toolkit = SQLDatabaseToolkit(db=db, llm=OpenAI(temperature=0))
agent_executor = create_sql_agent(
    llm=OpenAI(temperature=0),
    toolkit=toolkit,
    verbose=True
)
def generate_response(input_text):
  st.info(agent_executor.run(input_text))

with st.form('my_form'):
    text = st.text_area('Enter text:', 'What are the three key pieces of advice for learning how to code?')
    submitted = st.form_submit_button('Submit')
    if not openai_api_key.startswith('sk-'):
        st.warning('Please enter your OpenAI API key!', icon='⚠')
    if submitted and openai_api_key.startswith('sk-'):
        generate_response(text)