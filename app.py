from flask import Flask, render_template, request, redirect, url_for, jsonify, g, flash, session, Response, get_flashed_messages
from flask_login import login_required, LoginManager, login_user, UserMixin, logout_user, current_user
from langchain_pinecone import Pinecone
from pinecone import Pinecone as PineconeClient
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.messages import get_buffer_string
from operator import itemgetter
from langchain.schema import format_document
from langchain.memory import ConversationBufferMemory
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn.cluster import KMeans
import os
import tiktoken
from datetime import datetime
from dotenv import load_dotenv
from io import BytesIO
from PyPDF2 import PdfReader
import docx2txt
import requests
import re
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
import psycopg2
import bcrypt
from flask_session import Session
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import pickle
import stripe
from stripe.error import SignatureVerificationError
from azure.core.exceptions import ResourceNotFoundError
import json
from openai import OpenAI
from collections import defaultdict
from datetime import timedelta
from urllib.parse import urlparse
import redis

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key_here'

url = urlparse(os.environ.get('REDISCLOUD_URL'))

r = redis.Redis(host=url.hostname, port=url.port, password=url.password)

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = r

Session(app)

app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

AZURE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=eccoaiassets;AccountKey=utLcmZ0UjxcgspIkg6W52aVPJ1VszubHQO5YW/nI8jczhQBLloYezWkJl+cPaxbmPXsHHiI1KXg6+AStdbpA0w==;EndpointSuffix=core.windows.net"
connection_string = AZURE_CONNECTION_STRING
container_name = os.getenv('AZURE_CONTAINER_NAME')

stripe.api_key = os.getenv('STRIPE_API_KEY')
endpoint_secret = os.getenv('ENDPOINT_SECRET')

openai_api_key = os.getenv("OPENAI_API_KEY")

database_url = os.getenv('DATABASE_URL')

pinecone_api_key = os.getenv("PINECONE_API_KEY")
index_name= os.getenv("PINECONE_INDEX")
index_host = os.getenv("PINECONE_HOST")


pc = PineconeClient(api_key=pinecone_api_key)
index = pc.Index(index_name)
text_field="text"
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)


def get_bot_temperature(user_id, chatbot_id):
    with g.db_conn.cursor() as cursor:
        cursor.execute("SELECT bot_temperature FROM chatbot_settings WHERE user_id = %s AND id = %s;", (user_id, chatbot_id))
        row = cursor.fetchone()
        return row[0] if row else 0.0
    

def get_custom_prompt(user_id, chatbot_id):
    with g.db_conn.cursor() as cursor:
        cursor.execute("SELECT custom_prompt FROM chatbot_settings WHERE user_id = %s AND id = %s;", (user_id, chatbot_id))
        row = cursor.fetchone()
        return row[0] if row else "Default prompt part"
    
def get_LLM(user_id, chatbot_id):
    with g.db_conn.cursor() as cursor:
        cursor.execute("SELECT LLM FROM chatbot_settings WHERE user_id = %s AND id = %s;", (user_id, chatbot_id))
        row = cursor.fetchone()
        return row[0] if row else "gpt-3.5-turbo"


# Initialize Flask-Login
app.secret_key = os.getenv('SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)

class AuthenticatedUser(UserMixin):
    def __init__(self, id):
        self.id = id

@app.context_processor
def inject_user_name():
    if current_user.is_authenticated:
        user_id = current_user.id
        g.cursor.execute("""
        SELECT u."name"
        FROM public.users u
        WHERE u.id = %s;
        """, (user_id,))
        user_name = g.cursor.fetchone()
        if user_name:
            return {'name': user_name[0]}  # Assuming the name is in the first column
    return {'name': None}

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

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Check if email exists in the database
        g.cursor.execute("SELECT id, name FROM public.users WHERE email = %s", (email,))
        user_data = g.cursor.fetchone()
        if not user_data:
            flash('No account associated with that email address', 'error')
            return redirect(url_for('forgot_password'))

        # Generate a password reset token
        token = s.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

        # Save the token in the database
        g.cursor.execute("INSERT INTO public.password_resets (user_id, token) VALUES (%s, %s)", (user_data[0], token))
        g.db_conn.commit()

        # Create a password reset link with the token
        reset_link = url_for('reset_password', token=token, _external=True)

        # Send an email to the user with the reset link
        msg = Message('Password Reset Requested', recipients=[email])
        msg.html = render_template('reset_password_email.html', reset_link=reset_link, name=user_data[1])
        mail.send(msg)

        flash('Password reset link sent to your email address', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Validate the password reset token
        email = s.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=3600)
        app.logger.info(f"Email from token: {email}")
    except Exception as e:
        app.logger.error(f"Error validating token: {e}")
        flash('The password reset link is invalid or has expired', 'error')
        return redirect(url_for('login'))

    # Check if the token exists in the database
    g.cursor.execute("SELECT user_id FROM public.password_resets WHERE token = %s", (token,))
    user_data = g.cursor.fetchone()
    if not user_data:
        app.logger.error(f"Token not found in database: {token}")
        flash('The password reset link is invalid or has expired', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form['password']

        # Hash the new password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_password = hashed_password.decode('utf-8')

        # Update the user's password in the database
        g.cursor.execute("UPDATE public.users SET password = %s WHERE id = %s", (hashed_password, user_data[0]))
        g.db_conn.commit()

        # Delete the token from the database
        g.cursor.execute("DELETE FROM public.password_resets WHERE token = %s", (token,))
        g.db_conn.commit()

        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        
        g.cursor.execute("SELECT id, password FROM users WHERE LOWER(email) = %s", (email,))
        user_data = g.cursor.fetchone()
        
        if user_data:
            stored_password = user_data[1]
            if stored_password:
                try:
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        user = AuthenticatedUser(id=user_data[0])
                        login_user(user)
                        return redirect('/')
                    else:  # Passwords do not match
                        flash('Invalid password', 'error')
                except ValueError:  # Invalid bcrypt salt
                    flash('Invalid password', 'error')
            else:  
                flash('Invalid password', 'error')  # Stored Password is None
        else:
            flash('Invalid email', 'error')  # Change this line
            
    return render_template('login.html')

@app.route('/subscription', methods=['POST'])
def update_subscription():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']
    print(payload)
    print(sig_header)
    print(endpoint_secret)


    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Handle the event
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        subscription = event['data']['object']
        customer_email = subscription['customer_details']['email']
        customer_id = subscription['customer']
        custom_fields = subscription.get('custom_fields', [])
        print(custom_fields)
        customer_name = None

        for field in custom_fields:
            if field['key'] == 'name':
                customer_name = field['text']['value']
                break
        subscription_id = subscription['subscription']
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        subscription_item_id = stripe_subscription['items']['data'][0]['plan']['id']

        print(f'Customer Email: {customer_email}')
        print(f'Customer Name: {customer_name}')
        print(f'Stripe Customer ID: {customer_id}')
        print(f'Subscription ID: {subscription_id}')
        print(f'Subscription Item ID: {subscription_item_id}')

        # Check if user already exists
        g.cursor.execute("SELECT id FROM users WHERE email = %s", (customer_email,))
        user_data = g.cursor.fetchone()

        if user_data:
            # User exists, update their subscription_item_id
            g.cursor.execute("UPDATE users SET subscription_item_id = %s WHERE id = %s", (subscription_item_id, user_data[0]))
        else:
            # User does not exist, create a new user record
            g.cursor.execute("INSERT INTO users (email, name, subscription_item_id, stripe_customer_id) VALUES (%s, %s, %s, %s) RETURNING id", (customer_email, customer_name, subscription_item_id, customer_id))
            user_id = g.cursor.fetchone()[0]

            # Generate a password reset token
            token = s.dumps(customer_email, salt=app.config['SECURITY_PASSWORD_SALT'])

            # Save the token in the database
            g.cursor.execute("INSERT INTO public.password_resets (user_id, token) VALUES (%s, %s)", (user_id, token))
            g.db_conn.commit()

            # Create a password reset link with the token
            setup_link = url_for('reset_password', token=token, _external=True)

            # Send an email to the user with the reset link
            msg = Message('Account Setup', recipients=[customer_email])
            msg.html = render_template('setup_account.html', setup_link=setup_link, name=customer_name)
            mail.send(msg)

        # Get the renewal date from the subscription object
        renewal_date = datetime.fromtimestamp(stripe_subscription['current_period_end'])

        # Insert a new record into the usage table for the user, or update the existing record if it exists
        g.cursor.execute("INSERT INTO usage (user_id, subscription_item_id, renewal_date) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET subscription_item_id = %s, renewal_date = %s", (user_id, subscription_item_id, renewal_date, subscription_item_id, renewal_date))
        g.db_conn.commit()

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']

        # Set the user's subscription_item_id to null in the database
        g.cursor.execute("UPDATE users SET subscription_item_id = NULL WHERE stripe_customer_id = %s", (customer_id,))
        g.db_conn.commit()

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        plan_id = subscription['items']['data'][0]['plan']['id']

        # Get the renewal date from the subscription object
        renewal_date = datetime.fromtimestamp(subscription['current_period_end'])

        # Update the user's plan and renewal date in the usage table
        g.cursor.execute("UPDATE usage SET subscription_item_id = %s, renewal_date = %s WHERE user_id = (SELECT id FROM users WHERE stripe_customer_id = %s)", (plan_id, renewal_date, customer_id))
        
        # Update the subscription_item_id in the users table
        g.cursor.execute("UPDATE users SET subscription_item_id = %s WHERE stripe_customer_id = %s", (plan_id, customer_id))
        
        g.db_conn.commit()
    else:
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

@app.route('/', methods=['GET'])
@login_required
def home():
    # Fetch the chatbot settings for the current user
    g.cursor.execute("SELECT id, chatbot_name, created_at FROM chatbot_settings WHERE user_id = %s", (current_user.id,))
    chatbots = g.cursor.fetchall()

    g.cursor.execute("SELECT total_questions, total_answers FROM usage WHERE user_id = %s", (current_user.id,))
    result = g.cursor.fetchone()
    total_questions = result[0]
    total_answers = result[1]
    total_count = total_questions + total_answers

    # Fetch the user's plan
    g.cursor.execute("SELECT subscription_item_id FROM users WHERE id = %s", (current_user.id,))
    user_plan = g.cursor.fetchone()[0]

    # Fetch the user's Stripe customer ID
    g.cursor.execute("SELECT stripe_customer_id, name FROM users WHERE id = %s", (current_user.id,))
    result = g.cursor.fetchone()
    stripe_customer_id = result[0]
    name = result[1] if result[1] else 'User'

    # Fetch the subscriptions from Stripe
    subscriptions = stripe.Subscription.list(customer=stripe_customer_id)

    # Get the latest subscription
    latest_subscription = subscriptions.data[0]

    # Extract the renewal date
    renewal_date = datetime.fromtimestamp(latest_subscription.current_period_end)

    # Pass the chatbot settings to the template
    return render_template('home.html', chatbots=chatbots, count=total_count, user_id=current_user.id, user_plan=user_plan, renewal_date=renewal_date,name=name)

@app.route('/create_chatbot', methods=['POST'])
@login_required
def create_chatbot():
    user_id = current_user.id
    print(f"User ID: {user_id}")

    g.cursor.execute("SELECT COUNT(*) FROM chatbot_settings WHERE user_id = %s", (user_id,))
    chatbot_count = g.cursor.fetchone()[0]

    g.cursor.execute("SELECT subscription_item_id FROM users WHERE id = %s", (user_id,))
    user_plan = g.cursor.fetchone()[0]

    if user_plan == 'price_1P9FIULO2ToUaMQEmx2wG1qC' and chatbot_count >= 1:
        flash("You have exceeded your chatbot limit for the beginner plan!")
        return redirect(url_for('home'))
    elif user_plan == 'price_1OuIu1LO2ToUaMQE7Prun5Xt' and chatbot_count >= 3:
        flash("You have exceeded your chatbot limit for the intermediate plan!")
        return redirect(url_for('home'))
    elif user_plan == 'price_1OqKxhLO2ToUaMQEqRFU0dh9' and chatbot_count >= 5:
        flash("You have exceeded your chatbot limit for the enterprise plan!")
        return redirect(url_for('home'))

    default_settings = {
        'widget_icon_url': 'ecco_icon.png',  # Default widget icon URL
        'background_color': '#ffffff',  # Default background color
        'font_style': 'Arial',  # Default font style
        'bot_temperature': 0.3,  # Default bot temperature
        'greeting_message': 'Hello! I am Ecco, your AI assistant. How can I help you today?',  # Default greeting message
        'custom_prompt': """As "Ecco", your role is to provide friendly and humorous customer support for our company. Your knowledge is confined to the context provided, and you should strive to deliver accurate information about our company based on this context. Be as detailed as possible without fabricating answers. Politely decline to respond to any inquiries that are not related to the provided documents or our company. Maintain your character at all times. Respond in the language used in the incoming message. Use simple formatting in your responses and speak as a member of our team, using "we" and "us" instead of "they". Include hyperlinks when necessary. 
        RESTRICTIONS:
        Avoid using the phrase "Based on the given information".
        Do not invent answers. If you are uncertain about a response, say "I'm unsure about this. Could you please clarify or contact us for more information." and conclude your response there.
        """,
        'dot_color': '#555555',
        'logo': 'https://app.eccoai.org/static/images/ecco_icon.png',
        'chatbot_title': 'EccoAI',
        'title_color': '#BFEF4B',
        'border_color': '#ffffff',
        'chatbot_name': 'Chatbot',
        'primary_color': '#BFEF4B',
        'secondary_color': '#ffffff',
        'popup_message': 'Hello, I am here to answer your questions!',
        'LLM': 'gpt-3.5-turbo',
        'bot_bubble_color': '#dcdcdc',  # Default bot bubble color
        'user_bubble_color': '#5fc9f8'  # Default user bubble color
    }

    g.cursor.execute("""
            INSERT INTO chatbot_settings (user_id, widget_icon_url, background_color, font_style, bot_temperature, greeting_message, custom_prompt, dot_color, logo, chatbot_title, title_color, border_color, chatbot_name, primary_color, secondary_color, popup_message, LLM, bot_bubble_color, user_bubble_color)
            VALUES (%(user_id)s, %(widget_icon_url)s, %(background_color)s, %(font_style)s, %(bot_temperature)s, %(greeting_message)s, %(custom_prompt)s, %(dot_color)s, %(logo)s, %(chatbot_title)s, %(title_color)s, %(border_color)s, %(chatbot_name)s, %(primary_color)s, %(secondary_color)s, %(popup_message)s, %(LLM)s, %(bot_bubble_color)s, %(user_bubble_color)s)
            RETURNING id;
        """, {'user_id': user_id, **default_settings})
    chatbot_id = g.cursor.fetchone()[0]
    g.db_conn.commit()
    return jsonify({'url': url_for('admin', chatbot_id=chatbot_id, _external=True)})

@app.route('/delete_chatbot/<int:chatbot_id>', methods=['DELETE'])
@login_required
def delete_chatbot(chatbot_id):
    g.cursor.execute("""
        DELETE FROM chatbot_settings
        WHERE id = %s
    """, (chatbot_id,))
    g.db_conn.commit()
    return jsonify({'message': 'Chatbot deleted successfully'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("https://eccoai.org")

@app.route('/<int:user_id>/<int:chatbot_id>')
def chatbot(user_id, chatbot_id):
    print(f"session ID: {session.sid}")
    session[f'memory_{session.sid}'] = pickle.dumps(None)
    print()

    # Query PostgreSQL to get the settings
    g.cursor.execute("SELECT widget_icon_url, background_color, font_style, bot_temperature, greeting_message, custom_prompt, dot_color, logo, chatbot_title, title_color, border_color, primary_color, secondary_color, popup_message, LLM, bot_bubble_color, user_bubble_color, include_email_form FROM chatbot_settings WHERE user_id = %s AND id = %s;", (user_id, chatbot_id))
    row = g.cursor.fetchone()

    if row is None:
        return "No settings found for the given user_id and chatbot_id", 404

    settings = {
        'widget_icon': row[0],
        'background_color': row[1],
        'font_style': row[2],
        'bot_temperature': row[3],
        'greeting_message': row[4],
        'custom_prompt': row[5],
        'dot_color': row[6],
        'logo': row[7],
        'chatbot_title': row[8],
        'title_color': row[9],
        'border_color': row[10],
        'primary_color': row[11],
        'secondary_color': row[12],
        'popup_message': row[13],
        'LLM': row[14],
        'bot_bubble_color': row[15],  # Added bot_bubble_color
        'user_bubble_color': row[16],  # Added user_bubble_color
        'include_email_form': row[17]
    }

    g.cursor.execute("SELECT question, response FROM premade_questions WHERE user_id = %s AND chatbot_id = %s;", (user_id, chatbot_id,))
    questions = g.cursor.fetchall()
    print(questions)
    question_list = []
    if questions:
        for question in questions:
            question_dict = {
                "question": question[0],
                "response": question[1],
            }
            question_list.append(question_dict)

    return render_template('index.html', settings=settings, user_id=user_id, question_list=question_list)

@app.route('/<int:user_id>/<int:chatbot_id>/popup.js')
def serve_js(user_id, chatbot_id):
    # Query PostgreSQL to get the widget_icon_url and popup_message
    g.cursor.execute("SELECT widget_icon_url, popup_message, font_style FROM chatbot_settings WHERE user_id = %s AND id = %s;", (user_id, chatbot_id))
    row = g.cursor.fetchone()

    if row is None:
        return "No settings found for the given user_id and chatbot_id", 404

    # Pass in the widget_icon_url and popup_message
    settings = {
        'widget_icon': row[0],
        'popup_message': row[1],
        'font_style': row[2]
    }

    # Generate the JavaScript code
    js_code = f"""
    // chatbot.js

    // Function to inject the chatbot GUI into the website
    function injectChatbot() {{
        console.log('injectChatbot function called');
        var chatbotContainer = document.createElement('div');
        chatbotContainer.id = 'chatbotContainer';
        chatbotContainer.style.position = 'fixed';
        chatbotContainer.style.bottom = '20px';
        chatbotContainer.style.right = '20px';
        chatbotContainer.style.zIndex = '9999';
        chatbotContainer.style.backgroundColor = '#ffffff';
        chatbotContainer.style.border = '1px solid #ccc';
        chatbotContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
        
        var chatbotIframe = document.createElement('iframe');
        chatbotIframe.src = 'https://eccoai-customization-2--t0rfrt.herokuapp.com/{user_id}/{chatbot_id}';
        chatbotIframe.width = '360.5';
        chatbotIframe.height = '600';
        chatbotIframe.style.border = 'none';
        chatbotIframe.id = 'e';
        chatbotIframe.style.display = 'None';
        chatbotIframe.style.position = 'fixed';
        chatbotIframe.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
        chatbotIframe.style.zIndex = '9999';
        chatbotIframe.style.overflow = 'hidden';

        // Adjust styles based on window size
        function adjustIframeStyleForWindowSize() {{
            if (window.innerWidth <= 480) {{
                // Styles for iPhone or similar devices
                chatbotIframe.style.width = '100vw';
                chatbotIframe.style.height = '100vh';
                chatbotIframe.style.bottom = '0';
                chatbotIframe.style.right = '0';
                chatbotIframe.style.borderRadius = '0';
                chatbotIframe.style.position = 'fixed';
            }} else {{
                // Default styles for larger devices
                chatbotIframe.style.width = '360.5px';
                chatbotIframe.style.height = '600px';
                chatbotIframe.style.bottom = '100px';
                chatbotIframe.style.right = '10px';
                chatbotIframe.style.borderRadius = '10px';
                chatbotIframe.style.position = 'fixed';
            }}
        }}

        // Run the function on initial load
        adjustIframeStyleForWindowSize();

        // Add an event listener to run the function whenever the window is resized
        window.addEventListener('resize', adjustIframeStyleForWindowSize);
        
        var toggleButton = document.createElement('img');
        toggleButton.id = 'b';
        toggleButton.src = 'https://eccoai-customization-2--t0rfrt.herokuapp.com//static/images/{settings["widget_icon"]}';
        toggleButton.alt = 'Chat';
        toggleButton.style.width = '80px';
        toggleButton.style.height = '80px';
        toggleButton.style.position = 'fixed';
        toggleButton.style.bottom = '10px';
        toggleButton.style.right = '10px';
        toggleButton.style.zIndex = '1000';
        toggleButton.style.cursor = 'pointer';
        toggleButton.style.transition = 'transform 0.3s ease-in-out';

        var welcomeMessage = document.createElement('div');
        welcomeMessage.id = 'p';
        welcomeMessage.textContent = {json.dumps(settings["popup_message"])};
        welcomeMessage.style.fontFamily = '{settings["font_style"]}';
        welcomeMessage.style.display = 'block';
        welcomeMessage.style.color = 'black';
        welcomeMessage.style.position = 'fixed';
        welcomeMessage.style.bottom = '100px';
        welcomeMessage.style.right = '15px';
        welcomeMessage.style.zIndex = '10000';
        welcomeMessage.style.background = '#fff';
        welcomeMessage.style.border = '1px solid #ccc';
        welcomeMessage.style.padding = '10px';
        welcomeMessage.style.borderRadius = '5px';
        welcomeMessage.style.boxShadow = '0 0 10px rgba(0,0,0,.1)';

        var closeButton = document.createElement('span');
        closeButton.id = 'c';
        closeButton.style.display = 'none';
        closeButton.style.position = 'fixed';
        closeButton.style.bottom = '128px';
        closeButton.style.right = '10px';
        closeButton.style.zIndex = '10001';
        closeButton.style.cursor = 'pointer';
        closeButton.style.padding = '2px 6px';
        closeButton.style.borderRadius = '10px';
        closeButton.style.backgroundColor = '#dadada';
        closeButton.style.fontFamily = 'arial';
        closeButton.style.color = '#4e4e4e';
        closeButton.textContent = 'X';

        chatbotContainer.appendChild(welcomeMessage);
        chatbotContainer.appendChild(closeButton);
        chatbotContainer.appendChild(toggleButton);
        chatbotContainer.appendChild(chatbotIframe);
        document.body.appendChild(chatbotContainer);

        var p=document.getElementById('p'),c=document.getElementById('c'),b=document.getElementById('b');
        p.onmouseover=c.onmouseover=function(){{c.style.display='block'}};
        p.onmouseout=function(){{c.style.display='none'}};
        c.onclick=function(){{p.style.display=c.style.display='none'}};
        b.addEventListener('mouseover', function() {{
            this.style.transform = 'scale(1.1)';
        }});
        b.addEventListener('mouseout', function() {{
            this.style.transform = 'scale(1)';
        }});
        b.addEventListener('click', function() {{
        if (window.matchMedia('(max-width: 480px)').matches) {{
            this.style.display = 'none';
        }}
        var iframe = document.getElementById('e');
        if (iframe.style.display === 'none') {{
            iframe.style.display = 'block';
            iframe.style.opacity = 0;
            iframe.style.transformOrigin = 'bottom right';  
            iframe.style.transform = 'scale(0)'; // start from no size
            iframe.style.transition = 'transform 0.2s ease-out, opacity 0.2s ease-out'; // transition settings
            setTimeout(function() {{
                iframe.style.opacity = 1;
                iframe.style.transform = 'scale(1)'; // grow to full size
            }}, 0);
            p.style.display = 'none'; // hide the 'p' element
        }} else {{
            iframe.style.opacity = 0;
            iframe.style.transform = 'scale(0)'; // shrink to no size
            setTimeout(function() {{
                iframe.style.display = 'none';
            }}, 200); // after transition ends
        }}
        }});

        function closeChatbot() {{
            var iframe = document.getElementById('e');
            iframe.style.opacity = 0;
            iframe.style.transform = 'scale(0)'; // shrink to no size
            setTimeout(function() {{
                iframe.style.display = 'none';
            }}, 200); // after transition ends
        }}
    }}

    document.addEventListener('DOMContentLoaded', function() {{
        console.log('DOMContentLoaded event fired');
        injectChatbot();
    }});

    window.addEventListener('message', function(event) {{
    // Check if the message is from a trusted source
    if (event.origin === "https://eccoai-customization-2--t0rfrt.herokuapp.com") {{
        // Perform actions based on the message
        if (event.data === "closeIframe") {{
            var iframe = document.getElementById('e');
            var widget = document.getElementById('b');
            iframe.style.opacity = 0;
            iframe.style.transform = 'scale(0)'; // shrink to no size
            setTimeout(function() {{
                iframe.style.display = 'none'; // hide the iframe
                // Reappear logic for the widget
                widget.style.opacity = 1;
                widget.style.transform = 'scale(1)';
                widget.style.display = 'block'; // Adjust display style as needed
            }}, 200); // after transition ends
        }}
    }}
    }});
    """

    return Response(js_code, mimetype='text/javascript')

@app.route('/<int:user_id>/<int:chatbot_id>/get-session-data')
def get_session_data(user_id, chatbot_id):

    sessionid = session.sid

    # Fetch the email from the database where the sessionid matches
    g.cursor.execute("SELECT email, name FROM emails WHERE sessionid = %s;", (sessionid,))
    row = g.cursor.fetchone()

    if row is None:
        return jsonify({'message': 'No data found for the given session ID'}), 404

    # Pass in the email
    settings = {
        'email': row[0],
        'name': row[1]
    }
    print(settings)

    return jsonify(settings)

@app.route('/<int:user_id>/<int:chatbot_id>/save-email', methods=['POST'])
def save_email(user_id, chatbot_id):
    name = request.form.get('name')
    email = request.form.get('email')
    sessionid = session.sid
    ip_address = request.remote_addr  # Get the client's IP address

    # Validate the email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        return jsonify({'message': 'Invalid email format'}), 400

    # Insert the email into the database
    g.cursor.execute("INSERT INTO emails (user_id, chatbot_id, email, sessionid, ip_address, name) VALUES (%s, %s, %s, %s, %s, %s)", (user_id, chatbot_id, email, sessionid, ip_address, name))
    g.db_conn.commit()
    return jsonify({'message': 'Email saved successfully!'})

@app.route('/<int:user_id>/<int:chatbot_id>/chat', methods=['POST'])
def chat(user_id, chatbot_id):
    # Get the user's plan
    g.cursor.execute("SELECT subscription_item_id FROM users WHERE id = %s", (user_id,))
    user_plan = g.cursor.fetchone()[0]

    # Count the number of questions the user has asked
    g.cursor.execute("SELECT COUNT(*) FROM feedback WHERE user_id = %s", (user_id,))
    question_count = g.cursor.fetchone()[0]

    # Check if the user has exceeded their question limit
    if user_plan == 'price_1P9FIULO2ToUaMQEmx2wG1qC' and question_count >= 50:
        return jsonify({"status": "error", "message": "You have exceeded your question limit for the beginner plan!"})
    elif user_plan == 'price_1OuIu1LO2ToUaMQE7Prun5Xt' and question_count >= 500:
        return jsonify({"status": "error", "message": "You have exceeded your question limit for the intermediate plan!"})
    elif user_plan == 'price_1OqKxhLO2ToUaMQEqRFU0dh9' and question_count >= 10000:
        return jsonify({"status": "error", "message": "You have exceeded your question limit for the enterprise plan!"})

    vectorstore = Pinecone(
        index, embeddings, text_field,  namespace=f"{user_id}{chatbot_id}"
    )

    user_message = request.form.get('message')

    retriever = vectorstore.as_retriever(
            search_type = "similarity_score_threshold",
            search_kwargs={'score_threshold': 0.7, 'k': 3},
        )

    if f'memory_{session.sid}' in session:
        memory = pickle.loads(session[f'memory_{session.sid}'])
    else:
        memory = ConversationBufferMemory(
            return_messages=True, output_key="answer", input_key="question"
        )

    if memory is None:
        memory = ConversationBufferMemory(
            return_messages=True, output_key="answer", input_key="question"
        )

    bot_temperature = get_bot_temperature(user_id, chatbot_id)
    custom_prompt = get_custom_prompt(user_id, chatbot_id)
    model = get_LLM(user_id, chatbot_id)

    llm = ChatOpenAI(
        openai_api_key=openai_api_key,
        model_name=model,
        temperature=bot_temperature
    )

    DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

    def _combine_documents(
        docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
    ):
        doc_strings = [format_document(doc, document_prompt) for doc in docs]
        return document_separator.join(doc_strings)
    
    
    _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language. Do not alter the question if it's a simple phrase like "Okay!", "Cool!", "Sounds Good!", or "Thanks!".

    Chat History:
    {chat_history}
    Follow Up Question: {question}
    Standalone question:"""
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

    template = f"""{custom_prompt}

    Answer the question based only on the following context:
    {{context}}

    Question: {{question}}
    """
    ANSWER_PROMPT = ChatPromptTemplate.from_template(template)

    # First we add a step to load memory
    # This adds a "memory" key to the input object
    loaded_memory = RunnablePassthrough.assign(
        chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
    )
    # Now we calculate the standalone question
    standalone_question = {
        "standalone_question": {
            "question": lambda x: x["question"],
            "chat_history": lambda x: get_buffer_string(x["chat_history"]),
        }
        | CONDENSE_QUESTION_PROMPT
        | llm
        | StrOutputParser(),
    }
    # Now we retrieve the documents
    retrieved_documents = {
        "docs": itemgetter("standalone_question") | retriever,
        "question": lambda x: x["standalone_question"],
    }
    # Now we construct the inputs for the final prompt
    final_inputs = {
        "context": lambda x: _combine_documents(x["docs"]),
        "question": itemgetter("question"),
    }
    # And finally, we do the part that returns the answers
    answer = {
        "answer": final_inputs | ANSWER_PROMPT | ChatOpenAI(),
        "docs": itemgetter("docs"),
    }
    # And now we put it all together!
    final_chain = loaded_memory | standalone_question | retrieved_documents | answer

    inputs = {"question": user_message}
    config = {"metadata": {"session_id": session.sid}}
    result = final_chain.invoke(inputs, config=config)
    print(result)
    memory.save_context(inputs, {"answer": result["answer"].content})

    print("*"*100)
    print(session)
    print("*"*100)

    response = result['answer']
    docs = result['docs']
    # Convert the AIMessage to a dictionary
    sources = [{'source_url': doc.metadata['source_url'], 'filename': doc.metadata['filename']} for doc in docs]
    response_dict = {
        'content': response.content,
        'sources': sources,
        # Add any other fields as necessary
    }
    # Save the memory back to the session at the end of the request
    session[f'memory_{session.sid}'] = pickle.dumps(memory)

    # Print the contents of the memory
    print(f"Memory for user {session.sid}: {memory}")
    print("*"*100)
    print(response_dict)
    return jsonify(response_dict)

@app.route('/<int:chatbot_id>/conversations')
@login_required
def get_conversations(chatbot_id):
    user_id = current_user.id
    g.cursor.execute(
        "SELECT user_question, bot_response, feedback_type, created_at, sessionid, email, name FROM feedback WHERE user_id = %s AND chatbot_id = %s ORDER BY created_at DESC;",
        (user_id, chatbot_id)
    )

    rows = g.cursor.fetchall()
    conversations = {}

    for row in rows:
        session_id = row[4]
        if session_id not in conversations:
            conversations[session_id] = []
        created_at = row[3] - timedelta(hours=4)  # Subtract 4 hours
        conversations[session_id].append({
            'user_question': row[0],
            'bot_response': row[1],
            'feedback_type': row[2],
            'created_at': created_at.strftime('%I:%M %p %m/%d/%y'),
            'email': row[5],
            'name': row[6]
        })

    return render_template('conversations.html', chatbot_id=chatbot_id, conversations=conversations)

@app.route('/<int:user_id>/<int:chatbot_id>/store_feedback', methods=['POST'])
def store_feedback(user_id, chatbot_id):
    data = request.json
    feedback_type = data.get('feedback_type')
    bot_response = data.get('bot_response')
    user_question = data.get('user_question')
    record_id = data.get('id')  
    
    try:
        g.cursor.execute(
            "UPDATE feedback SET user_question = %s, bot_response = %s, feedback_type = %s, user_id = %s, chatbot_id = %s WHERE id = %s",
            (user_question, bot_response, feedback_type, user_id, chatbot_id, record_id)
        )
        g.db_conn.commit()
        return jsonify({"message": "Feedback stored successfully!"})
    except Exception as e:
        print(f"Error storing feedback: {e}")
        return jsonify({"message": "Error storing feedback"}), 500

@app.route('/<int:user_id>/<int:chatbot_id>/store_qa', methods=['POST'])
def store_qa(user_id, chatbot_id):
    data = request.json
    question = data.get('question')
    answer = data.get('answer')
    session_id = session.sid

    try:
        # Fetch the name, email, and ip_address from the emails table
        g.cursor.execute(
            "SELECT name, email, ip_address FROM emails WHERE user_id = %s AND chatbot_id = %s AND sessionid = %s",
            (user_id, chatbot_id, session_id)
        )
        result = g.cursor.fetchone()
        name = result[0] if result else None
        email = result[1] if result else None
        ip_address = result[2] if result else None

        g.cursor.execute(
            "INSERT INTO feedback (user_question, bot_response, user_id, chatbot_id, sessionid, feedback_type, name, email, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (question, answer, user_id, chatbot_id, session_id, None, name, email, ip_address)
        )
        record_id = g.cursor.fetchone()[0]

        # Update the usage table
        g.cursor.execute(
            "UPDATE usage SET total_questions = total_questions + 1, total_answers = total_answers + 1 WHERE user_id = %s",
            (user_id,)
        )

        g.db_conn.commit()
        return jsonify({"message": "Question and answer stored successfully!", "id": record_id})
    except Exception as e:
        print(f"Error storing question and answer: {e}")
        return jsonify({"message": "Error storing question and answer"}), 500

@app.route('/<int:chatbot_id>/admin')
@login_required
def admin(chatbot_id):
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        # Redirect to the login page
        return redirect(url_for('login'))

    # Query PostgreSQL to get the list of documents
    g.cursor.execute("SELECT id, filename, file_size, upload_date FROM document_mapping WHERE user_id = %s AND chatbot_id = %s;", (user_id, chatbot_id))
    documents = [{'id': row[0], 'name': row[1], 'size': round(row[2], 3), 'date_added': row[3]} for row in g.cursor.fetchall()]

    return render_template('admin.html', documents=documents, user_id=user_id, chatbot_id=chatbot_id)
@app.route('/<int:chatbot_id>/integrations')
@login_required
def integrations(chatbot_id):
    user_id = current_user.id
    return render_template('integrations.html', user_id=user_id, chatbot_id=chatbot_id)

@app.route('/<int:chatbot_id>/upload', methods=['POST'])
def upload_file(chatbot_id):
    uploaded_files = request.files.getlist('file')
    user_id = current_user.id
    total_file_size = 0

    g.cursor.execute("SELECT SUM(file_size) FROM document_mapping WHERE user_id = %s", (user_id,))
    store_file_size = g.cursor.fetchone()[0]
    if store_file_size is None:
        store_file_size = 0
    print(store_file_size)

    for file in uploaded_files:
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_size = len(file.read())
            
            # Reset the file position to the beginning
            file.seek(0)

            file_size = file_size/1000000
            total_file_size += file_size

    g.cursor.execute("SELECT subscription_item_id FROM users WHERE id = %s", (user_id,))
    user_plan = g.cursor.fetchone()[0]
    print(user_plan)

    # Check if the user has exceeded their file size limit
    if (user_plan == 'price_1P9FIULO2ToUaMQEmx2wG1qC' and total_file_size + float(store_file_size) > 5) or \
        (user_plan == 'price_1OuIu1LO2ToUaMQE7Prun5Xt' and total_file_size + float(store_file_size) > 25) or \
        (user_plan == 'price_1OqKxhLO2ToUaMQEqRFU0dh9' and total_file_size + float(store_file_size) > 1024):  # 1 GB is 1024 MB
         return jsonify({"status": "error", "message": "File size exceeds the limit for your plan!"})

    for file in uploaded_files:
        if file.filename != '':
            filename = secure_filename(file.filename)

            # Modify the filename to include the user_id and chatbot_id
            unique_filename = f"{user_id}_{chatbot_id}_{filename}"

            # Create a blob client using the unique file name as the name for the blob
            blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
            blob_client = blob_service_client.get_blob_client(container_name, unique_filename)

            # Upload the file
            blob_client.upload_blob(file, blob_type="BlockBlob", content_settings=ContentSettings(content_type='application/pdf'))
            source_url = blob_client.url

            file_size = len(file.read())

            # Reset the file position to the beginning
            file.seek(0)

            file_size = file_size/1000000

            g.cursor.execute("INSERT INTO document_mapping (filename, file_size, user_id, chatbot_id) VALUES (%s, %s, %s, %s) RETURNING id;", (filename, file_size, user_id, chatbot_id))
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
                    text = text.replace('\n', ' ')  # replace newline characters with space
                    process_text(text, filename, page_num, f"{user_id}", f"{chatbot_id}", f"{source_url}")

            elif file_extension == "docx":
                doc = docx2txt.process(file_stream)
                cleaned_doc = re.sub(r'\s+', ' ', doc.strip())
                process_text(cleaned_doc, filename, 0,f"{user_id}", f"{chatbot_id}", f"{source_url}")

    return jsonify({"status": "success", "message": "Files uploaded successfully!"})

def process_text(text, filename, page_num, user_id, chatbot_id, source_url):
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
        upsert_data = [(chunk_doc_id, embedding, {"filename": filename, "text": text_chunk, "source_url": source_url})]
        
        # Store the embeddings in Pinecone using 'upsert' method
        index.upsert(upsert_data, namespace=f"{user_id}{chatbot_id}")

def process_excel_text(full_text, headers, filename,user_id, chatbot_id):
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
        index.upsert(upsert_data, namespace=f"{user_id}{chatbot_id}")


@app.route('/<int:chatbot_id>/scrape', methods=['POST'])
@login_required
def scrape_url(chatbot_id):
    url = request.form['url']
    user_id = current_user.id
    try:
        response = requests.get(url)
        raw_html = response.text
        print(f"Raw HTML: {raw_html}")  # Print raw HTML

        soup = BeautifulSoup(raw_html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text
        text = soup.get_text()
        print(f"Text after removing script and style elements: {text}")  # Print text after removing script and style elements

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        print(f"Final text: {text}")  # Print final text

        # Calculate file size
        file_size = len(text.encode('utf-8'))/1000000
        print(f"File size: {file_size}")  # Print file size

        # Insert into database
        g.cursor.execute("INSERT INTO document_mapping (filename, file_size, user_id, chatbot_id) VALUES (%s, %s, %s, %s) RETURNING id;", (url, file_size, user_id, chatbot_id))
        g.db_conn.commit()

        # Process the text and put it in the vector database
        process_text(text, url, 0, f"{user_id}", f"{chatbot_id}", f"{url}")

        return redirect(url_for('admin', chatbot_id=chatbot_id))

    except requests.RequestException as e:
        return jsonify({"status": "error", "message": f"Error processing URL: {str(e)}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"})

@app.route('/<int:chatbot_id>/delete/<doc_id>', methods=['POST'])
@login_required
def delete(chatbot_id, doc_id):
    user_id = current_user.id
    # Delete from PostgreSQL
    g.cursor.execute("DELETE FROM document_mapping WHERE id = %s AND user_id = %s RETURNING filename;", (doc_id, user_id))
    result = g.cursor.fetchone()
    g.db_conn.commit()
    if result:
        filename = result[0]
        unique_filename = f"{user_id}_{chatbot_id}_{filename}"
        prefix = f"{filename}_"
        print(f"Deleted entry for ID {doc_id} from the database")

        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container_name, unique_filename)
        try:
            blob_client.delete_blob()
            print(f"Blob deleted for filename {unique_filename}")
        except ResourceNotFoundError:
            print(f"Blob not found for filename {unique_filename}")

        namespace = f"{user_id}{chatbot_id}"
        list_url = f"https://{index_host}/vectors/list?namespace={namespace}&prefix={prefix}"
        delete_url = f"https://{index_host}/vectors/delete"

        headers = {
            "Api-Key": pinecone_api_key,
            "Content-Type": "application/json"
        }

        list_response = requests.get(list_url, headers=headers)
        if list_response.status_code == 200:
            ids_to_delete = [record['id'] for record in list_response.json().get('vectors', [])]
            if ids_to_delete:
                delete_response = requests.post(
                    delete_url, 
                    headers=headers, 
                    json={
                        "ids": ids_to_delete,
                        "namespace": namespace
                    }
                )
                if delete_response.status_code == 200:
                    print(f"Deleted vectors with IDS {ids_to_delete} from Pinecone")
        else:
            print(f"Error listing record from Pincone")
    else:
        print(f"File not found")

    return redirect(url_for('admin', chatbot_id=chatbot_id))

@app.route('/<int:chatbot_id>/settings')
@login_required
def settings(chatbot_id):
    user_id = current_user.id

    g.cursor.execute("SELECT subscription_item_id FROM users WHERE id = %s", (user_id,))
    user_plan = g.cursor.fetchone()[0]

    g.cursor.execute("SELECT widget_icon_url, background_color, font_style, bot_temperature, greeting_message, custom_prompt, dot_color, logo, chatbot_title, title_color, border_color, primary_color, secondary_color, popup_message, chatbot_name, LLM, bot_bubble_color, user_bubble_color, include_email_form FROM chatbot_settings WHERE user_id = %s AND id = %s;", (user_id, chatbot_id,))
    row = g.cursor.fetchone()

    settings = {
        'widget_icon': row[0],
        'background_color': row[1],
        'font_style': row[2],
        'bot_temperature': row[3],
        'greeting_message': row[4],
        'custom_prompt': row[5],
        'dot_color': row[6],
        'logo': row[7],
        'chatbot_title': row[8],
        'title_color': row[9],
        'border_color': row[10],
        'primary_color': row[11],
        'secondary_color': row[12],
        'popup_message': row[13],
        'chatbot_name': row[14],
        'LLM': row[15],
        'bot_bubble_color': row[16],  # Added bot_bubble_color
        'user_bubble_color': row[17],  # Added user_bubble_color
        'include_email_form': row[18]
    }

    # Fetch the pre-made questions and answers
    g.cursor.execute("SELECT id, question, response FROM premade_questions WHERE user_id = %s AND chatbot_id = %s;", (user_id, chatbot_id,))
    premade_questions = g.cursor.fetchall()

    return render_template('settings.html', settings=settings, user_id=user_id, user_plan=user_plan, chatbot_id=chatbot_id, premade_questions=premade_questions)

def update_chatbot_settings_in_db(chatbot_id, widget_icon, background_color, font_style, bot_temperature, greeting_message, custom_prompt, dot_color, logo, chatbot_title, title_color, border_color, primary_color, secondary_color, popup_message, chatbot_name, llm, bot_bubble_color, user_bubble_color, include_email_form):
    user_id = current_user.id
    sql = """
    UPDATE chatbot_settings
    SET widget_icon_url = %s, background_color = %s, font_style = %s, bot_temperature = %s, greeting_message = %s, custom_prompt = %s, dot_color = %s, logo = %s, chatbot_title = %s, title_color = %s, border_color = %s, primary_color = %s, secondary_color = %s, popup_message = %s, chatbot_name = %s, LLM = %s, bot_bubble_color = %s, user_bubble_color = %s, include_email_form = %s WHERE user_id = %s AND id = %s;
    """

    g.cursor.execute(sql, (widget_icon, background_color, font_style, bot_temperature, greeting_message, custom_prompt, dot_color, logo, chatbot_title, title_color, border_color, primary_color, secondary_color, popup_message, chatbot_name, llm, bot_bubble_color, user_bubble_color, include_email_form, user_id, chatbot_id)) 
    g.db_conn.commit()

@app.route('/delete_question', methods=['DELETE'])
def delete_question():
    question_id = request.json.get('question_id')
    g.cursor.execute("DELETE FROM premade_questions WHERE id = %s;", (question_id,))
    g.db_conn.commit()
    return jsonify({"message": "Question deleted successfully!"})

def insert_new_premade_question_in_db(chatbot_id, question, response):
    user_id = current_user.id
    query = """
    INSERT INTO premade_questions (user_id, chatbot_id, question, response)
    VALUES (%s, %s, %s, %s)
    """
    params = (user_id, chatbot_id, question, response)
    g.cursor.execute(query, params)
    g.db_conn.commit()

def question_exists_in_db(chatbot_id, question):
    g.cursor.execute("SELECT 1 FROM premade_questions WHERE chatbot_id = %s AND question = %s;", (chatbot_id, question))
    return g.cursor.fetchone() is not None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'png'

def get_existing_logo_url(chatbot_id):
    g.cursor.execute("SELECT logo FROM chatbot_settings WHERE id = %s;", (chatbot_id,))
    return g.cursor.fetchone()[0]

@app.route('/<int:chatbot_id>/update_chatbot_settings', methods=['POST'])
def update_chatbot_settings(chatbot_id):
    user_id = current_user.id
    # Process the logo file first, if it exists
    logo_url = None  # Default to None in case no logo is uploaded
    if 'logo' in request.files:
        file = request.files['logo']
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Modify the filename to include the user_id and chatbot_id
            unique_filename = f"{user_id}_{chatbot_id}_{filename}"

            # Create a blob client using the unique file name as the name for the blob
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=unique_filename)

            # Check if the file already exists in the blob storage
            try:
                blob_client.get_blob_properties()
                flash('Please upload a different logo.', 'error')
                return redirect(url_for('settings', chatbot_id=chatbot_id))
            except ResourceNotFoundError:
                # The file does not exist in the blob storage, so we can upload it
                pass

            blob_client.upload_blob(file, blob_type="BlockBlob", content_settings=ContentSettings(content_type='image/png', content_disposition='inline'))

            logo_url = blob_client.url

            # Delete the old logo
            old_logo_url = get_existing_logo_url(chatbot_id)
            if old_logo_url:
                old_logo_filename = old_logo_url.split('/')[-1]
                old_logo_blob_client = blob_service_client.get_blob_client(container=container_name, blob=old_logo_filename)
                try:
                    old_logo_blob_client.delete_blob()
                except ResourceNotFoundError:
                    # The old logo file does not exist in the blob storage, so we can ignore this error
                    pass
    
    # Process the rest of the form data
    widget_icon = request.form.get('icon-select')
    background_color = request.form.get('background_color')
    font_style = request.form.get('font_style')
    bot_temperature = request.form.get('bot_temperature')
    greeting_message = request.form.get('greeting_message')
    custom_prompt = request.form.get('custom_prompt')
    dot_color = request.form.get('dot_color')
    chatbot_title = request.form.get('chatbot_title')
    title_color = request.form.get('title_color')
    border_color = request.form.get('border_color')
    primary_color = request.form.get('primary')
    secondary_color = request.form.get('secondary')
    popup_message = request.form.get('popup_message')
    premade_questions = request.form.getlist('premade_questions[]')
    premade_responses = request.form.getlist('premade_responses[]')
    chatbot_name = request.form.get('chatbot_name')
    llm = request.form.get('bot_LLM')
    bot_bubble_color = request.form.get('bot_bubble_color')
    user_bubble_color = request.form.get('user_bubble_color')
    include_email_form = request.form.get('include_email_form')

    for question, response in zip(premade_questions, premade_responses):
        if not question_exists_in_db(chatbot_id, question):
            insert_new_premade_question_in_db(chatbot_id, question, response)

    # If a new logo was uploaded, override the existing logo URL
    # If a new logo was uploaded, use its URL, otherwise use the existing logo URL
    logo = logo_url if logo_url else get_existing_logo_url(chatbot_id)

    update_chatbot_settings_in_db(chatbot_id, widget_icon, background_color, font_style, bot_temperature, greeting_message, custom_prompt, dot_color, logo, chatbot_title, title_color, border_color, primary_color, secondary_color, popup_message, chatbot_name, llm, bot_bubble_color, user_bubble_color, include_email_form)

    flash('Chatbot settings updated successfully!', 'success')
    return redirect(url_for('settings', chatbot_id=chatbot_id))

@app.route('/<int:user_id>/<int:chatbot_id>/greeting_message')
def greeting_message(user_id, chatbot_id):
    # Query PostgreSQL to get the greeting message for the user with id = 1
    g.cursor.execute("SELECT greeting_message FROM chatbot_settings WHERE user_id = %s AND id = %s;", (user_id, chatbot_id))
    row = g.cursor.fetchone()
    if row is None:
        greeting_message = 'Hello, how can I help?'  # Default value if no greeting message is found for the user
    else:
        greeting_message = row[0]
    return jsonify(greeting_message=greeting_message)



@app.route('/<int:chatbot_id>/analytics')
@login_required
def analytics(chatbot_id):
    user_id = current_user.id
    g.cursor.execute("SELECT user_question, bot_response, feedback_type, created_at, email, ip_address, sessionid, name FROM feedback WHERE user_id = %s AND chatbot_id = %s;", (user_id, chatbot_id))
    rows = g.cursor.fetchall()

    # Fetch the total number of questions and responses from the usage table
    g.cursor.execute("SELECT total_questions, total_answers, subscription_item_id FROM usage WHERE user_id = %s;", (user_id,))
    usage_row = g.cursor.fetchone()
    total_questions_responses = usage_row[0] + usage_row[1]
    subscription_item_id = usage_row[2]

    # Determine the user's plan based on the subscription item id
    plans = {
        'price_1P9FIULO2ToUaMQEmx2wG1qC': 50,
        'price_1OuIu1LO2ToUaMQE7Prun5Xt': 500,
        'price_1OqKxhLO2ToUaMQEqRFU0dh9': 10000
    }
    user_plan = plans.get(subscription_item_id, 0)

    # Calculate the remaining percentage and round to two decimal places
    remaining_percentage = round(((total_questions_responses) / user_plan) * 100, 2) if user_plan else 0

    if not rows:
        return render_template('analytics.html', data=[], common_topics=None, chatbot_id=chatbot_id)

    questions_and_responses = [row[0] + ' ' + row[1] for row in rows]
    emails = [row[4] for row in rows if row[4] is not None]
    unique_email_count = len(set(emails))

    session_ids = [row[6] for row in rows if row[6] is not None]
    unique_session_count = len(set(session_ids))


    #!!!!!!!!!!!!!!!!!!!!
    # If you want to use the OpenAI API to get common topics, uncomment the code below
    #!!!!!!!!!!!!!!!!!!!!
    # client = OpenAI(
    #     api_key=openai_api_key
    # )

    # Combine all questions and responses into a single string
    all_text = ' '.join(questions_and_responses)

    # if all_text:
    #     completion = client.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {"role": "system", "content": "You are a helpful assistant, skilled in analyzing a list of topics and providing 5 common topics from that list. When providing the topics, only list the topics without any additional text."},
    #             {"role": "user", "content": f"Create a list of 3 common topics from the following text. They must be no longer than 1 word. Make the list of topics in a numbered order: {all_text}."}
    #         ]
    #     )
    #     topics = completion.choices[0].message.content.replace('- ', '')
    #     common_topics = topics.split('\n')
    # else:
    #     common_topics = ["No questions asked yet"]
    common_topics = ["No questions asked yet"]

    print(f"Common topics: {common_topics}")

    data = []
    if rows:
        for row in rows:
            created_at = row[3] - timedelta(hours=4)  # Subtract 4 hours
            data.append({
                'user_question': row[0],
                'bot_response': row[1],
                'feedback_type': row[2],
                'created_at': created_at.strftime('%I:%M %p\n%m/%d/%y'),  # Changed format here
                'email': row[4],
                'ip_address': row[5],
                'sessionid': row[6],
                'name': row[7]
            })
    else:
        data = []
    date_count = defaultdict(int)



    if rows:
        for row in rows:
            date = row[3].strftime('%m/%d') 
            date_count[date] += 1  

    return render_template('analytics.html', data=data, common_topics=common_topics, chatbot_id=chatbot_id, unique_email_count=unique_email_count, unique_session_count=unique_session_count, remaining_percentage=remaining_percentage, date_count=json.dumps(date_count))

#!!!!!!!!!!!!!!!!!!!!
#route not being used
#!!!!!!!!!!!!!!!!!!!!
@app.route('/delete_feedback', methods=['POST'])
@login_required
def delete_feedback():
    user_id = current_user.id
    user_question = request.form.get('user_question')
    bot_response = request.form.get('bot_response')

    g.cursor.execute("DELETE FROM feedback WHERE user_id = %s AND user_question = %s AND bot_response = %s;", (user_id, user_question, bot_response))
    g.conn.commit()

    flash('Feedback successfully deleted', 'success')

    return redirect(url_for('analytics'))

#!!!!!!!!!!!!!!!!!!!!
#route not being used
#!!!!!!!!!!!!!!!!!!!!
@app.route('/analytics/data')
@login_required
def analytics_data():
    user_id = current_user.id
    # Fetch the number of likes from the database
    g.cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'Like' AND user_id = %s;", (user_id,))
    likes = g.cursor.fetchone()[0]

    # Fetch the number of dislikes from the database
    g.cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'Dislike' AND user_id = %s;", (user_id,))
    dislikes = g.cursor.fetchone()[0]

    # Fetch the number of none feedback from the database
    g.cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type IS NULL AND user_id = %s;", (user_id,))
    none = g.cursor.fetchone()[0]

    # Return the data as JSON
    return jsonify({'likes': likes, 'dislikes': dislikes, 'none': none})

@app.errorhandler(401)
def unauthorized_access(e):
    # note that we set the 401 status explicitly
    return render_template('error.html', message="Unauthorized access."), 401

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('error.html', message="Page not found."), 404

@app.errorhandler(500)
def internal_server_error(e):
    # note that we set the 500 status explicitly
    return render_template('error.html', message="An unexpected error has occurred. Please try again later."), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use PORT if it's there
    app.run(host='0.0.0.0', port=port, debug=False)  # Set host to '0.0.0.0'