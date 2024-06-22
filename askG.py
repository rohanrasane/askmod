import os
import base64
import json
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import gspread
from google.oauth2 import service_account
import pandas as pd
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key

PANEL_QUESTIONS_SHEET_ID = '1Z6xYRHIK6acEU4enmNLyR7jtTMMS86I3LgrqRoeHO-M'  # Replace with your panel questions Google Sheet ID
GOOGLE_SHEET_ID = '1UmKe0yqeeZXi1wnbeVIkd_lpLInBTmdXgyynaKaqygQ'  # Replace with your actual Google Sheet ID

def get_mod_pwd():
    return os.environ.get("MODERATOR_PASSWORD")

def create_keyfile_dict():
    variables_keys = {
        "type": os.environ.get("SHEET_TYPE"),
        "project_id": os.environ.get("SHEET_PROJECT_ID"),
        "private_key_id": os.environ.get("SHEET_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("SHEET_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.environ.get("SHEET_CLIENT_EMAIL"),
        "client_id": os.environ.get("SHEET_CLIENT_ID"),
        "auth_uri": os.environ.get("SHEET_AUTH_URI"),
        "token_uri": os.environ.get("SHEET_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.environ.get("SHEET_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.environ.get("SHEET_CLIENT_X509_CERT_URL"),
        "universe_domain": os.environ.get("SHEET_UNIVERSE_DOMAIN")
    }
    return variables_keys

# Google Sheets authentication
def get_gspread_client():
    creds_dict = create_keyfile_dict()
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    client = gspread.authorize(scoped_creds)
    return client

# Load panelist questions from Google Sheets
def load_panel_questions():
    client = get_gspread_client()
    sheet = client.open_by_key(PANEL_QUESTIONS_SHEET_ID).sheet1
    records = sheet.get_all_records()
    return records

# Load attendee questions from Google Sheets
def load_attendee_questions():
    client = get_gspread_client()
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    records = sheet.get_all_records()
    # Sort records based on upvotes in descending order
    sorted_records = sorted(records, key=lambda x: x['upvotes'], reverse=True)
    return sorted_records

# Save a new attendee question to Google Sheets
def save_attendee_question(name, question):
    client = get_gspread_client()
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    new_data = [str(uuid.uuid4()), name, question, 0]
    sheet.append_row(new_data)

# Upvote an attendee question
def upvote_attendee_question(question_id):
    client = get_gspread_client()
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    records = sheet.get_all_records()
    for i, record in enumerate(records):
        if record['id'] == question_id:
            record['upvotes'] += 1
            sheet.update_cell(i + 2, 4, record['upvotes'])  # Adjust based on your sheet's structure
            break

@app.route('/')
def home():
    return redirect(url_for('moderator_login'))

@app.route('/moderator')
def moderator():
    if 'moderator' in session:
        return render_template('index.html')
    return redirect(url_for('moderator_login'))

@app.route('/attendee')
def attendee():
    return render_template('attendee.html')

@app.route('/attendee', methods=['POST'])
def submit_attendee_question():
    data = request.get_json()
    name = data['name']
    question = data['question']
    save_attendee_question(name, question)
    return jsonify({'status': 'success'})

@app.route('/attendee/questions', methods=['GET'])
def get_attendee_questions():
    questions = load_attendee_questions()
    return jsonify(questions)

@app.route('/attendee/upvote/<question_id>', methods=['POST'])
def upvote_attendee_question_route(question_id):
    upvote_attendee_question(question_id)
    return jsonify({'status': 'success'})

@app.route('/questions', methods=['GET'])
def get_questions():
    questions = load_panel_questions()
    return jsonify(questions)

@app.route('/moderator/login', methods=['GET', 'POST'])
def moderator_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == get_mod_pwd():
            session['moderator'] = True
            return redirect(url_for('moderator'))
        else:
            return render_template('moderator_login.html', error='Invalid password')
    return render_template('moderator_login.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
