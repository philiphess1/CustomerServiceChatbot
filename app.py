from flask import Flask, render_template, request, redirect, url_for, jsonify, g, flash, session
from flask_login import login_required, LoginManager, login_user, UserMixin, logout_user
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
from werkzeug.utils import secure_filename
import psycopg2
import bcrypt
from flask_session import Session



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
prompt_template = """"You are an AI-powered HR assistant for Indiana University. Your primary function is to provide accurate, detailed, and comprehensive information about the university's HR policies, benefits, procedures, and any other related HR queries provided by the user's QUESTION. You have access to CONTEXT that contains HR information about Indiana University related to the user's QUESTION. Please note that if there is no relevant information in the available context, you should not make up an answer and instead inform the user that you are unable to provide a response given their question. Never say "based on CONTEXT" or something similar to that.
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
    session.clear()
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
    g.cursor.execute("SELECT id, filename FROM document_mapping;")  # Use g.cursor here
    documents = [{'id': row[0], 'name': row[1]} for row in g.cursor.fetchall()]  # And here

    return render_template('admin.html', documents=documents)

@app.route('/upload', methods=['POST'])
def upload_file():

    uploaded_files = request.files.getlist('file')
    for file in uploaded_files:
        if file.filename != '':
            filename = secure_filename(file.filename)

            g.cursor.execute("INSERT INTO document_mapping (filename) VALUES (%s) RETURNING id;", (filename,))
            g.db_conn.commit()

            # Create a BytesIO stream from the uploaded file
            file_stream = BytesIO(file.read())

            # Use PyPDF2 to read the PDF from the BytesIO stream
            pdf_reader = PdfReader(file_stream)
            num_pages = len(pdf_reader.pages)

            # Loop through each page
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                # Process the text (i.e., break it into chunks and create embeddings)
                chunk_size = 750
                overlap = 100
                for start in range(0, len(text), chunk_size - overlap):
                    end = start + chunk_size
                    text_chunk = text[start:end]

                    # Generate embeddings
                    embedding = embeddings.embed_query(text_chunk)

                    # Create a chunk ID
                    chunk_doc_id = f"{filename}_page{page_num}_start{start}:{end}"

                    # Prepare data for Pinecone
                    upsert_data = [(chunk_doc_id, embedding, {"filename": filename, "text": text_chunk})]
                    
                    # Store the embeddings in Pinecone using 'upsert' method
                    index.upsert(upsert_data)

    return jsonify({"status": "success", "message": "Files uploaded successfully!"})

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