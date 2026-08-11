from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import random
import json
import fitz  # PyMuPDF
import google.generativeai as genai
from werkzeug.utils import secure_filename
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Load interview questions from the JSON file
with open('questions.json') as f:
    questions = json.load(f)

# Configure app for file uploads (resume analyzer)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Assuming 'uploads' is in the same directory as app.py
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Helper function: Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Helper function: Extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        return ''.join(page.get_text() for page in doc)
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None

    # Helper function: Generate analysis using GenAI


def generate_analysis(text):
    try:
        api_key = os.getenv('GENAI_API_KEY', 'AIzaSyC8-JlVu0sG399e0i-i3ZIz8p6gVOxZMpc')  # Replace with your actual API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            [f"Analyze this resume and highlight skills, improvements, and achievements:\n{text}"])
        return response.text
    except Exception as e:
        logging.error(f"Error generating analysis: {e}")
        return "Error: Unable to analyze the resume."

    # Flask route: Index page (Landing Page)


@app.route('/')
def index():
    return render_template('landing.html')


# Flask route: Resume analyzer form
@app.route('/resume', methods=['GET', 'POST'])
def resume_analyzer():
    if request.method == 'POST':
        file = request.files.get('resume')
        if not file:
            return 'No file part', 400
        if file.filename == '':
            return 'No selected file', 400
        if not allowed_file(file.filename):
            return 'File type not allowed', 400

        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            if filepath.endswith('.pdf'):
                text = extract_text_from_pdf(filepath)
            else:
                with open(filepath, 'r') as f:
                    text = f.read()

            analysis = generate_analysis(text)

            # Code to remove unwanted characters
            alldata = ""
            for i in analysis:
                if i != '*':
                    alldata = alldata + i
            analysis = alldata

            return render_template('resume_result.html', analysis=analysis)
        except Exception as e:
            logging.error(f"Error processing resume: {e}")
            return 'Error processing resume', 500

    return render_template('resume_index.html')


# Flask route: Resume analysis result page
@app.route('/result')
def result():
    analysis = request.args.get('analysis', '')
    formatted_analysis = '<br>'.join(
        f"<strong style='color:green;'>{line}</strong>" if "Skills" in line else
        f"<span style='color:red;'>{line}</span>" if "Improvement" in line else
        f"<span style='color:blue;'>{line}</span>" if "Achievements" in line else
        line
        for line in analysis.split('\n')
    )

    return render_template('resume_result.html', analysis=formatted_analysis)


# Flask route: Interview questions generation
@app.route('/interview', methods=['GET', 'POST'])
def interview():
    return render_template('interview_index.html')


@app.route('/generate', methods=['POST'])
def generate():
    category = request.form.get('category')
    if category and category in questions:
        question = random.choice(questions[category])
        return jsonify({'question': question})
    else:
        return jsonify({'error': 'Invalid category. Please choose from \'technical\' or \'behavioral\''})


if __name__ == "__main__":
    app.run(debug=True)