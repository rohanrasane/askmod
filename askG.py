import os
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import gspread
from google.oauth2 import service_account
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key

PANEL_QUESTIONS_SHEET_IDS = {
    1007: '1Z6xYRHIK6acEU4enmNLyR7jtTMMS86I3LgrqRoeHO-M',  # innovation
    8085: '1JxclR4A23a11HMAG7JMc_3yzh2LwbjLWBLJMg5xk2vA',  # semi
    1010: '1aANU1b8D_UEWSlLfez_N2xQ-1DmycRO9KUvZB8qundE',  # cyber
    2008: '1myWVrLf7-20YsSCZqch-yiTRCZ1V_2ovSAZCrtaVSvQ',  # wep
    # Add more panels as needed
}
GOOGLE_SHEET_ID = {
    1007: '1UmKe0yqeeZXi1wnbeVIkd_lpLInBTmdXgyynaKaqygQ',  # Panel 1 Sheet ID
    8085: '1KV9ejInqh9r-akB3FVvI20Z9HCobX6tItUtyfuYcy-E',  # Replace with Panel 2 Sheet ID
    1010: '17RsWzfHMM4_YQvk_eoqVkldT7i8jgf6cR185vcJz_r8',  # Replace with Panel 2 Sheet ID
    2008: '1yaaHL2Fn7NyFHXpXbxyTh4_rEbiOuu6uvv1Q1KFlGqU',  # Replace with Panel 2 Sheet ID
    # Add more panels as needed
}
PANEL_NAMES ={
    1007: "Innovation Panel",
    8085: "Semi-conductor Panel",
    1010: "Cyber Security Panel",
    2008: "Women Entrepreneurship Panel"
}
# Decorator to check if user is logged in
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session['logged_in']:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('moderator_login', panel_number=kwargs.get('panel_number')))
    wrap.__name__ = f.__name__
    return wrap

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
def load_panel_questions(panel_number):
    client = get_gspread_client()
    sheet_id = PANEL_QUESTIONS_SHEET_IDS.get(panel_number)
    if sheet_id:
        sheet = client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()
        return records
    else:
        return []

# Load attendee questions from Google Sheets
def load_attendee_questions(panel_number):
    client = get_gspread_client()
    sheet_id = GOOGLE_SHEET_ID.get(panel_number)
    if sheet_id:
        sheet = client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()
        sorted_records = sorted(records, key=lambda x: x['upvotes'], reverse=True)
        return sorted_records
    else:
        return []


# Save a new attendee question to Google Sheets
def save_attendee_question(panel_number, name, question):
    client = get_gspread_client()
    sheet_id = GOOGLE_SHEET_ID.get(panel_number)
    sheet = client.open_by_key(sheet_id).sheet1
    new_data = [str(uuid.uuid4()), name, question, 0]
    sheet.append_row(new_data)

# Upvote an attendee question
def upvote_attendee_question(panel_number, question_id):
    client = get_gspread_client()
    sheet_id = GOOGLE_SHEET_ID.get(panel_number)
    sheet = client.open_by_key(sheet_id).sheet1
    records = sheet.get_all_records()
    for i, record in enumerate(records):
        if record['id'] == question_id:
            record['upvotes'] += 1
            sheet.update_cell(i + 2, 4, record['upvotes'])  # Adjust based on your sheet's structure
            break

@app.route('/<int:panel_number>')
def home(panel_number):
    return redirect(url_for('moderator_login', panel_number=panel_number))

@app.route('/moderator/<int:panel_number>')
@login_required
def moderator(panel_number):
    return render_template('index.html', panel_number=panel_number)

@app.route('/attendee/<int:panel_number>')
def attendee(panel_number):
    return render_template('attendee.html', panel_number=panel_number)

@app.route('/attendee/<int:panel_number>', methods=['POST'])
def submit_attendee_question(panel_number):
    data = request.get_json()
    name = data['name']
    question = data['question']
    save_attendee_question(panel_number, name, question)
    return jsonify({'status': 'success'})

@app.route('/attendee/<int:panel_number>/questions', methods=['GET'])
def get_attendee_questions(panel_number):
    questions = load_attendee_questions(panel_number)
    panel_details = {
        "name":  PANEL_NAMES.get(panel_number, "GENERIC PANEL"),
        "questions": questions
    }
    return jsonify(panel_details)

@app.route('/attendee/<int:panel_number>/upvote//<question_id>', methods=['POST'])
def upvote_attendee_question_route(panel_number, question_id):
    upvote_attendee_question(panel_number, question_id)
    return jsonify({'status': 'success'})

@app.route('/questions/<int:panel_number>', methods=['GET'])
@login_required
def get_questions(panel_number):
    questions = load_panel_questions(panel_number)
    panel_details = {
        "name":  PANEL_NAMES.get(panel_number, "GENERIC PANEL"),
        "questions": questions
    }
    return jsonify(panel_details)

@app.route('/moderator/login/<int:panel_number>', methods=['GET', 'POST'])
def moderator_login(panel_number):
    print(panel_number)
    if request.method == 'POST':
        password = request.form['password']
        if password == get_mod_pwd():
            session['logged_in'] = True
            return redirect(url_for('moderator', panel_number=panel_number))
        else:
            return render_template('moderator_login.html', panel_number=panel_number, error='Invalid password')
    return render_template('moderator_login.html', panel_number=panel_number)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
