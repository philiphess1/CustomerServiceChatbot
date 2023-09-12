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

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

document_id_mapping = {}

def generate_document_id():
    """Generate a unique document ID."""
    max_id = max(document_id_mapping.keys()) if document_id_mapping else 0
    return max_id + 1

# @app.route('/')
# def index():
#     # Create a list of documents with IDs and names
#     documents = [{'id': doc_id, 'name': filename} for doc_id, filename in document_id_mapping.items()]
#     return render_template('index.html', documents=documents)

# @app.route('/upload', methods=['POST'])
# def upload():
#     uploaded_files = request.files.getlist('document')

#     for file in uploaded_files:
#         if file.filename != '':
#             filename = secure_filename(file.filename)
#             # Generate a unique document ID and store the mapping
#             doc_id = generate_document_id()
#             document_id_mapping[doc_id] = filename
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

#     return redirect(url_for('index'))

# @app.route('/delete/<int:doc_id>')
# def delete(doc_id):
#     if doc_id in document_id_mapping:
#         filename = document_id_mapping.pop(doc_id, None)
#         if filename:
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             if os.path.exists(file_path):
#                 os.remove(file_path)
#                 print(f"Deleted file: {file_path}")
#         else:
#             print(f"File not found for ID {doc_id}")

#     return redirect(url_for('index'))

pinecone_api_key = os.getenv("PINECONE_API_KEY")
environment = os.getenv("PINECONE_ENVIRONMENT")
openai_api_key = os.getenv("OPENAI_API_KEY")

users = {1: {'id': 1, 'username': 'philip', 'password': 'password'}}

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

pinecone.init(api_key=pinecone_api_key, environment=environment)
index = pinecone.Index("hrbot")
#print("Type of index:", type(index))

vectorstore = Pinecone(index, embeddings.embed_query, "text")

app.secret_key = 'secretkey'
login_manager = LoginManager()
login_manager.init_app(app)

class AuthenticatedUser(UserMixin):
    def __init__(self, id):
        self.id = id

# def get_vector_store():
#     index_name = "my_vector_store"
#     pinecone.deinit()
#     pinecone.init(api_key=pinecone_api_key)
    
#     if index_name not in pinecone.list_indexes():
#         pinecone.create_index(name=index_name, metric="cosine", shards=1)
    
#     index = pinecone.Index(index_name=index_name)
#     return index

# Existing routes ...

# # Query route for RAG
# @app.route('/query', methods=['POST'])
# def query():
#     query_text = request.form['query_text']
#     vector_store = get_vector_store()

#     # Fetch top-N similar document IDs from Pinecone
#     top_ids, _ = vector_store.query(queries=[query_text], top_k=5)
#     top_ids = top_ids[0]

#     # Retrieve the original text corresponding to these document IDs
#     # Assume you have a function `get_text_by_ids` that does this
#     retrieved_texts = get_text_by_ids(top_ids)
    
#     # Now query OpenAI with the retrieved text as context
#     prompt_with_context = f"Query: {query_text}\nContext: {retrieved_texts}"
    
#     response = openai.Completion.create(
#         engine="text-davinci-003",
#         prompt=prompt_with_context,
#         max_tokens=100,
#         top_p=1.0,
#         frequency_penalty=0,
#         presence_penalty=0,
#     )
    
#     answer = response.choices[0].text.strip()
    
#     return render_template('result.html', answer=answer)

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
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
@login_required
def admin():
    documents = [{'id': doc_id, 'name': filename} for doc_id, filename in document_id_mapping.items()]
    return render_template('admin.html', documents=documents)

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_files = request.files.getlist('file')  # This should match the name attribute in your HTML form
    for file in uploaded_files:
        if file.filename != '':
            filename = secure_filename(file.filename)
            # Generate a unique document ID and store the mapping
            doc_id = generate_document_id()
            document_id_mapping[doc_id] = filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Open the saved file and create a BytesIO stream
            with open(file_path, "rb") as f:
                file_stream = BytesIO(f.read())

            # Initialize Pinecone
            pinecone.init(api_key=pinecone_api_key, environment=environment)
            index = pinecone.Index("hrbot")

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

                    # Create a document ID
                    chunk_doc_id = f"{filename}_page{page_num}_start{start}"

                    upsert_data = [(chunk_doc_id, embedding, {"filename": filename})]

                    # Store the embeddings in Pinecone using 'upsert' method
                    index.upsert(upsert_data)
    return redirect(url_for('admin'))
# def upload_file():
#     uploaded_files = request.files.getlist('file') # This should match the name attribute of your input tag in your HTML form

#     for file in uploaded_files:
#         if file.filename != '':
#             filename = secure_filename(file.filename)
#             # Generate a unique document ID and store the mapping
#             doc_id = generate_document_id()
#             document_id_mapping[doc_id] = filename
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(file_path)

#             with open(file_path, "rb") as f:
#                 file_stream = BytesIO(f.read())

#     pinecone.init(api_key=pinecone_api_key, environment=environment)
#     index = pinecone.Index("hrbot")
#     #print(f"Type of index within upload_file: {type(index)}")
#     file = request.files['file']
#     file_stream = BytesIO(file.read())

#     # Use PyPDF2 to read the PDF
#     pdf_reader = PdfReader(file_stream)
#     num_pages = len(pdf_reader.pages)
    
#     # Loop through each page
#     for page_num in range(num_pages):
#         page = pdf_reader.pages[page_num]
#         text = page.extract_text()

#         # Process the text (i.e., break it into chunks and create embeddings)
#         chunk_size = 1000
#         overlap = 200
#         for start in range(0, len(text), chunk_size - overlap):
#             end = start + chunk_size
#             text_chunk = text[start:end]
            
#             # Generate embeddings (Assuming you have a method to generate embeddings)
#             embedding = embeddings.embed_query(text_chunk)
            
#             #print(f"Embedding for doc_id source_page{page_num}_start{start}: {embedding}")
            

#             # Create a document ID
#             doc_id = f"{file.filename}_page{page_num}_start{start}"

#             upsert_data = [(doc_id, embedding, {"filename": file.filename})]
            
#             # Print the upsert data to the console for inspection
            
            
#             # Store the embeddings in Pinecone using 'upsert' method
#             index.upsert(upsert_data)  # Note the use of 'upsert' here

@app.route('/delete/<doc_id>', methods=['POST'])
@login_required
def delete(doc_id):
    if doc_id in document_id_mapping:
            filename = document_id_mapping.pop(doc_id, None)
            if filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
            else:
                print(f"File not found for ID {doc_id}")
    return redirect(url_for('admin'))

def query_database_for_documents():
    return [{"id": 1, "name": "doc1"}, {"id": 2, "name": "doc2"}]

def delete_document_from_database(doc_id):
    pass

if __name__ == '__main__':
    app.run(debug=True)
