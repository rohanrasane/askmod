from flask import Flask, jsonify, render_template, request
import pandas as pd
import os
import uuid

app = Flask(__name__)

PANEL_QUESTIONS_FILE = 'questions.xlsx'
ATTENDEE_QUESTIONS_FILE = 'attendee_questions.xlsx'

# Load panelist questions from Excel file
def load_panel_questions():
    if os.path.exists(PANEL_QUESTIONS_FILE):
        df = pd.read_excel(PANEL_QUESTIONS_FILE)
        return df.to_dict('records')
    return []

# Load attendee questions from Excel file
def load_attendee_questions():
    if os.path.exists(ATTENDEE_QUESTIONS_FILE):
        df = pd.read_excel(ATTENDEE_QUESTIONS_FILE)
        return df.to_dict('records')
    return []

# Save a new attendee question to Excel file
def save_attendee_question(name, question):
    new_data = {
        'id': str(uuid.uuid4()),
        'name': name,
        'question': question,
        'upvotes': 0
    }

    if os.path.exists(ATTENDEE_QUESTIONS_FILE):
        try:
            df = pd.read_excel(ATTENDEE_QUESTIONS_FILE)
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        except ValueError:
            os.remove(ATTENDEE_QUESTIONS_FILE)
            df = pd.DataFrame([new_data])
    else:
        df = pd.DataFrame([new_data])
    
    df.to_excel(ATTENDEE_QUESTIONS_FILE, index=False)

# Upvote an attendee question
def upvote_attendee_question(question_id):
    if os.path.exists(ATTENDEE_QUESTIONS_FILE):
        try:
            df = pd.read_excel(ATTENDEE_QUESTIONS_FILE)
            df.loc[df['id'] == question_id, 'upvotes'] += 1
            df.to_excel(ATTENDEE_QUESTIONS_FILE, index=False)
        except ValueError:
            os.remove(ATTENDEE_QUESTIONS_FILE)

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True, port=8123)
