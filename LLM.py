from dotenv import load_dotenv
import os
import google.generativeai as genai
import mysql.connector
import streamlit as st
import logging
import pandas as pd
from collections import deque

class AIModel:
    def __init__(self, api_key, model_name, generation_config, safety_settings):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name, safety_settings=safety_settings)
        self.generation_config = generation_config

    def get_response(self, prompt):
        responses = self.model.generate_content(
            prompt,
            generation_config=self.generation_config,
            stream=True,
        )
        query = ""
        for response in responses:
            query += response.text
        return query

class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor=self.connection.cursor(buffered=True)
            logging.info("Successfully connected to the database.")
        except mysql.connector.Error as err:
            logging.error(f"Error: {err}")
            st.error(f"Database connection failed: {err}")

    def execute_query(self, query):
        try:
            self.cursor.execute(query)
            self.connection.commit()
            columns = []
            if self.cursor!= []:
                for x in self.cursor:
                    columns.append(x)
            df=pd.DataFrame(columns)
            st.write(df)
            logging.info("Query executed successfully.")
            return "Query executed successfully."
        
        except mysql.connector.Error as err:
            logging.error(f"Error: `{err}`")
            st.error(f"Some error raised, check log file")
        except:
            st.write("`executed`")
            

def setup_logging():
    logging.basicConfig(filename="app.log", 
                        level=logging.INFO, 
                        format="%(asctime)s:%(levelname)s:%(message)s")
def read_last_lines(filename, lines_count):
    with open(filename, 'r') as file:
        return ''.join(deque(file, maxlen=lines_count))
    
def main():
    load_dotenv()
    setup_logging()
    
    database=st.text_input("Enter Database")
    if database:
            
        st.write(f"*`Working on {database} database`*")
        api_key = os.getenv("GOOGLE_API_KEY")
        ai_model = AIModel(
            api_key=api_key,
            model_name="gemini-pro",
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                top_p=0.5,
                top_k=32,
                candidate_count=1,
                max_output_tokens=1000,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )

        db_manager = DatabaseManager(
            host="localhost",
            user="root",
            password="ayon_0611",
            database=database
        )

        db_manager.connect()

        st.title("Query Language Generator (QLG)")
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []


        with st.form("sql_form"):
            user_input = st.text_area("Enter your prompt:")
            submit_button = st.form_submit_button(label="Generate and Execute SQL")

        if submit_button and user_input:
            prompt = f"""
            {user_input}
            Generate a valid SQL command based on the above description that I can directly paste in SQL sheet.
            - Output the SQL command only, with no additional text or explanations.
            - Ensure the command is a single line without any newline or escape sequences.
            - Do not include any comments or unnecessary whitespace.
            """
            st.session_state['chat_history'].append(("``USER``", user_input))
            query = ai_model.get_response(prompt)
            st.write(f"Generated SQL Query: `{query}`")

            execution_result = db_manager.execute_query(query)
            st.write(execution_result)
            st.session_state['chat_history'].append(("``QLG``", f"`{query}`"))
        
        with st.sidebar:
            on=st.toggle("View Conversation History")
            if on:
                for role, text in st.session_state['chat_history']:
                    st.write(f"{role}: {text}")

        with st.sidebar:
            on=st.toggle("View Logs")
            if on:
                st.title("Logs")
                last_lines = read_last_lines("app.log", 5)
                st.text(last_lines)
        
        with st.sidebar:
            
            st.write("*`Developed by Ayon and Saksham`*")
    
if __name__ == "__main__":
    main()
