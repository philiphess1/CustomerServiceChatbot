from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_required, LoginManager, login_user, UserMixin, logout_user
from langchain.vectorstores import Pinecone
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
import os
from dotenv import load_dotenv
from io import BytesIO
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
import openai
import psycopg2



load_dotenv()

app = Flask(__name__)

pinecone_api_key = os.getenv("PINECONE_API_KEY")
environment = os.getenv("PINECONE_ENVIRONMENT")
openai_api_key = os.getenv("OPENAI_API_KEY")
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

pinecone.init(api_key=pinecone_api_key, environment=environment)
index = pinecone.Index("hrbot")
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

# Connect to PostgreSQL database
db_conn = psycopg2.connect(
    dbname=db_name,
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port
)
cursor = db_conn.cursor()

# Initialize Flask-Login
app.secret_key = 'secretkey'
login_manager = LoginManager()
login_manager.init_app(app)
users = {1: {'id': 1, 'username': 'philip', 'password': 'password'}}

class AuthenticatedUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    user_data = users.get(int(user_id))
    if user_data:
        return AuthenticatedUser(id=user_data['id'])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Manually authenticate the user
        if username == 'philip' and password == 'password':
            user = AuthenticatedUser(id=1)
            login_user(user)
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
@login_required
def admin():
    # Query PostgreSQL to get the list of documents
    cursor.execute("SELECT id, filename FROM document_mapping;")
    documents = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    return render_template('admin.html', documents=documents)

@app.route('/upload', methods=['POST'])
def upload_file():

    uploaded_files = request.files.getlist('file')
    for file in uploaded_files:
        if file.filename != '':
            filename = secure_filename(file.filename)

            # Insert this mapping into PostgreSQL
            cursor.execute("INSERT INTO document_mapping (filename) VALUES (%s) RETURNING id;", (filename,))
            #doc_id = cursor.fetchone()[0]
            db_conn.commit()

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
                chunk_size = 1000
                overlap = 200
                for start in range(0, len(text), chunk_size - overlap):
                    end = start + chunk_size
                    text_chunk = text[start:end]

                    # Generate embeddings
                    embedding = embeddings.embed_query(text_chunk)

                    # Create a chunk ID
                    chunk_doc_id = f"{filename}_page{page_num}"

                    # Prepare data for Pinecone
                    upsert_data = [(chunk_doc_id, embedding, {"filename": filename})]

                    # Store the embeddings in Pinecone using 'upsert' method
                    index.upsert(upsert_data)

    return redirect(url_for('admin'))

@app.route('/delete/<doc_id>', methods=['POST'])
@login_required
def delete(doc_id):
    # Delete from PostgreSQL
    cursor.execute("DELETE FROM document_mapping WHERE id = %s RETURNING filename;", (doc_id,))
    result = cursor.fetchone()
    db_conn.commit()
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
    app.run(debug=True)