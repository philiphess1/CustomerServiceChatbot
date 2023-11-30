from flask import Flask, render_template, request, redirect, url_for, jsonify, g, flash, session
from flask_login import login_required, LoginManager, login_user, UserMixin, logout_user, current_user
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
import pinecone
import os
import tiktoken
from dotenv import load_dotenv
from io import BytesIO
from PyPDF2 import PdfReader
import docx2txt
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
import psycopg2
import bcrypt
from flask_session import Session
import pandas as pd



load_dotenv()

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'your_secret_key_here'
Session(app)

pinecone_api_key = os.getenv("PINECONE_API_KEY")
environment = os.getenv("PINECONE_ENVIRONMENT")
openai_api_key = os.getenv("OPENAI_API_KEY")
database_url = os.getenv('DATABASE_URL')

pinecone.init(api_key=pinecone_api_key, environment=environment)
index_name= os.getenv("PINECONE_INDEX")
index = pinecone.Index(index_name)
text_field="text"
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

vectorstore = Pinecone(
    index, embeddings.embed_query, text_field
)

llm = ChatOpenAI(
    openai_api_key=openai_api_key,
    model_name='gpt-3.5-turbo',
    temperature=0.3
)

# Define the prompt template with placeholders for context and chat history
prompt_template = """
    You are an AI-powered assistant designed to provide precise and comprehensive information about Beber Summer Camp's policies, benefits, procedures, and related queries. 
    Your main role is to assist users by addressing their specific questions related to Beber Summer Camp. You will offer me accurate answers based only on your knowledge about Beber Summer Camp. 
    If you don't have relevant information in your context regarding a user's question, you should inform the user that you are unable to provide an answer to that specific query and suggest contacting info@bebercamp.com or (847) 677-7130. 
    Do not fabricate responses. Decline to answer any question not related to Beber Summer Camp or its documents. Maintain your character consistently. Always reply in the language of the user's message. Use straightforward formatting. 
    Respond as if you are a member of the Beber Summer Camp team, using 'we' and 'us' instead of 'they'. Provide hyperlinks when necessary.

    CONTEXT: {context}

    QUESTION: {question}"""

# Create a PromptTemplate object with input variables for context and chat history
TEST_PROMPT = PromptTemplate(input_variables=["context", "question"], template=prompt_template)

# Create a ConversationBufferMemory object to store the chat history
memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=8)

# Create a ConversationalRetrievalChain object with the modified prompt template and chat history memory
conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": TEST_PROMPT}
    )

# Connect to PostgreSQL database


db_conn = psycopg2.connect(database_url)
cursor = db_conn.cursor()

# Initialize Flask-Login
app.secret_key = os.getenv('SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)

class AuthenticatedUser(UserMixin):
    def __init__(self, id):
        self.id = id

@app.route('/clear_memory_session', methods=['POST'])
def clear_memory():
    # Clear the memory
    # session.clear()
    memory.clear()
    conversation_history = session.get('conversation_history', [])
    conversation_history.clear()
    print(f"session ID: {session.sid}")
    print()
    return jsonify({"message": "Memory and session cleared successfully"})


@app.before_request
def before_request():
    g.db_conn = psycopg2.connect(database_url)
    g.cursor = g.db_conn.cursor()

@app.teardown_request
def teardown_request(exception):
    cursor = getattr(g, 'cursor', None)
    if cursor is not None:
        cursor.close()
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is not None:
        db_conn.close()

@login_manager.user_loader
def load_user(user_id):
    g.cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    user_data = g.cursor.fetchone()
    if user_data:
        return AuthenticatedUser(id=user_data[0])
    return None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        g.cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if g.cursor.fetchone():
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_password = hashed_password.decode('utf-8')

        # Insert new user into the database
        g.cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        g.db_conn.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        g.cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user_data = g.cursor.fetchone()
        
        if user_data:
            stored_password = user_data[1]
            if stored_password:
                try:
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        user = AuthenticatedUser(id=user_data[0])
                        login_user(user)
                        return redirect(url_for('admin'))
                    else:  # Passwords do not match
                        flash('Invalid password', 'error')
                except ValueError:  # Invalid bcrypt salt
                    flash('Invalid password', 'error')
            else:  
                flash('Invalid password', 'error')  # Stored Password is None
        else:
            flash('Invalid username', 'error')  # User Data is None
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
def home():
    # session.clear()
    memory.clear()
    print(f"session ID: {session.sid}")
    print()
    return render_template('index.html')

@app.route('/IU_HR')
def HR():
    return render_template('IU_HR.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message')
    
    # Load the conversation history from session
    conversation_history = session.get('conversation_history', [])
    
    # Handle the user input and get the response
    response = conversation_chain.run({'question': user_message})
    
    # Save the user message and bot response to session
    conversation_history.append({'input': user_message, 'output': response})
    session['conversation_history'] = conversation_history
    
    # print(f"User: {user_message} | Bot:{response}")  # This will print the conversation history
    print(conversation_history)
    print(session)
    print("*"*100)
    
    return jsonify(response=response)

@app.route('/store_feedback', methods=['POST'])
def store_feedback():
    data = request.json
    feedback_type = data.get('feedback_type')
    bot_response = data.get('bot_response')
    user_question = data.get('user_question')
    
    try:
        g.cursor.execute(
            "INSERT INTO feedback (user_question, bot_response, feedback_type) VALUES (%s, %s, %s)",
            (user_question, bot_response, feedback_type)
        )
        g.db_conn.commit()
        return jsonify({"message": "Feedback stored successfully!"})
    except Exception as e:
        print(f"Error storing feedback: {e}")
        return jsonify({"message": "Error storing feedback"}), 500


@app.route('/admin')
@login_required
def admin():
    # Query PostgreSQL to get the list of documents
    user_id = current_user.id
    g.cursor.execute("SELECT id, filename, file_size, upload_date FROM document_mapping WHERE user_id = %s;", (user_id,)) # Use g.cursor here
    documents = [{'id': row[0], 'name': row[1], 'size': round(row[2], 3), 'date_added': row[3]} for row in g.cursor.fetchall()]  # And here

    return render_template('admin.html', documents=documents)

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_files = request.files.getlist('file')
    user_id = current_user.id
    for file in uploaded_files:
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_size = len(file.read())  # Read the content of the file once
            
            # Reset the file position to the beginning
            file.seek(0)

            file_size = file_size/1000000

            g.cursor.execute("INSERT INTO document_mapping (filename, file_size, user_id) VALUES (%s, %s, %s) RETURNING id;", (filename, file_size, user_id))
            g.db_conn.commit()

            # Create a BytesIO stream from the uploaded file
            file_stream = BytesIO(file.read())
            file_extension = filename.split(".")[-1].lower()

            if file_extension == "pdf":
                pdf_reader = PdfReader(file_stream)
                num_pages = len(pdf_reader.pages)
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    process_text(text, filename, page_num)

            elif file_extension == "docx":
                doc = docx2txt.process(file_stream)
                cleaned_doc = re.sub(r'\s+', ' ', doc.strip())
                process_text(cleaned_doc, filename, 0)

            elif file_extension == "xlsx":
                # use pandas to read the excel file from the bytesIO steam
                df = pd.read_excel(file_stream)
                headers = ' '.join(df.columns) + '\n'
                full_text = df.to_string(index=False, header=False)
                process_excel_text(full_text, headers, filename)

            elif file_extension == "csv":
                # use pandas to read the excel file from the bytesIO steam
                encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_stream, encoding=encoding)
                        headers = ' '.join(df.columns) + '\n'
                        full_text = df.to_string(index=False, header=False)
                        process_excel_text(full_text, headers, filename)
                        break
                    except UnicodeDecodeError:
                        continue
                    except pd.errors.EmptyDataError:
                        return jsonify({"status": "error", "message": "File is empty or incorrectly formatted!"})
            
    return jsonify({"status": "success", "message": "Files uploaded successfully!"})

def process_text(text, filename, page_num):
    # Process the text (i.e., break it into chunks and create embeddings)
    chunk_size = 750
    overlap = 100
    for start in range(0, len(text), chunk_size - overlap):
        end = start + chunk_size
        text_chunk = text[start:end]
        print(text_chunk)

        # Generate embeddings
        embedding = embeddings.embed_query(text_chunk)

        # Create a chunk ID
        chunk_doc_id = f"{filename}_page{page_num}_start{start}:{end}"

        # Prepare data for Pinecone
        upsert_data = [(chunk_doc_id, embedding, {"filename": filename, "text": text_chunk})]
        
        # Store the embeddings in Pinecone using 'upsert' method
        index.upsert(upsert_data)

def process_excel_text(full_text, headers, filename):
    chunk_size = 750
    overlap = 100
    for start in range(0, len(full_text), chunk_size - overlap):
        end = start + chunk_size
        text_chunk = full_text[start:end]
        text_chunk = headers + text_chunk
        print(text_chunk)
        # Generate embeddings
        embedding = embeddings.embed_query(text_chunk)

        # Create a chunk ID
        chunk_doc_id = f"{filename}_start{start}:{end}"


        # Prepare data for Pinecone
        upsert_data = [(chunk_doc_id, embedding, {"filename": filename, "text": text_chunk})]
        
        # Store the embeddings in Pinecone using 'upsert' method
        index.upsert(upsert_data)


@app.route('/scrape', methods=['POST'])
def scrape_url():
    url = request.form['url']  # Get the URL from the form data
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        raw_text = soup.get_text()
        text = re.sub(r'\s+', ' ', raw_text.strip())
        process_text(text, url, 0)
        return jsonify({"status": "success", "message": "URL scraped and processed successfully!"})
    else:
        return jsonify({"status": "error", "message": "Failed to scrape URL."})

@app.route('/delete/<doc_id>', methods=['POST'])
@login_required
def delete(doc_id):
    # Delete from PostgreSQL
    g.cursor.execute("DELETE FROM document_mapping WHERE id = %s RETURNING filename;", (doc_id,))
    result = g.cursor.fetchone()
    g.db_conn.commit()
    if result:
        filename = result[0]  # Assuming filename is the first element returned
        print(f"Deleted entry for ID {doc_id} from the database")

        # Delete from Pinecone
        delete_filter = {
            "filename": {"$eq": filename}
        }
        index.delete(filter=delete_filter)
        print(f"Deleted vectors with filename {filename} from Pinecone")

    else:
        print(f"File not found for ID {doc_id}")

    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use PORT if it's there
    app.run(host='0.0.0.0', port=port, debug=False)  # Set host to '0.0.0.0'