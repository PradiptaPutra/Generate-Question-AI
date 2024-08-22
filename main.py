from flask import Flask, request, jsonify
from openai import OpenAI
import os
import fitz  # PyMuPDF
import json

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = Flask(__name__)

# Set your OpenAI API key
MODEL = "gpt-4o-mini"  # Or another suitable model that supports function calling

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(pdf_file) as doc:
        for page in doc:
            text += page.get_text()
    return text

# Generate prompt for OpenAI API
def generate_prompt(subject: str, level: str, num_questions: int, question_type: str, context: str) -> str:
    return f"""Create {num_questions} high-quality {question_type} questions in Bahasa Indonesia for a {subject} exam at the {level} level for Indonesian students.
    Consider the following guidelines:
    1. Ensure the questions are aligned with the Indonesian national curriculum (Kurikulum Nasional).
    2. Use contexts, examples, and scenarios that are familiar to Indonesian students.
    3. Include references to Indonesian culture, geography, history, or daily life where appropriate.
    4. Ensure language use is appropriate for the specified education level in Indonesia.
    5. For multiple-choice questions, provide 4 options (A, B, C, D).
    6. Provide detailed explanations or rubrics in Bahasa Indonesia.
    7. Use the appropriate terminology for the subject as it would be taught in Indonesian schools.

    Context for generating questions:
    {context}"""

# Define function schema for question generation
def define_function(question_type: str):
    return {
        "name": "generate_exam_questions",
        "description": "Generate exam questions for Indonesian students",
        "parameters": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "level": {"type": "string"},
                "question_type": {"type": "string", "enum": ["multiple_choice", "essay"]},
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "choices": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "option": {"type": "string"},
                                        "text": {"type": "string"}
                                    }
                                }
                            } if question_type == "multiple_choice" else {},
                            "correct_answer": {"type": "string"} if question_type == "multiple_choice" else {},
                            "explanation": {"type": "string"} if question_type == "multiple_choice" else {},
                            "sample_answer": {"type": "string"} if question_type == "essay" else {},
                            "rubric": {"type": "string"} if question_type == "essay" else {}
                        },
                        "required": ["question"]
                    }
                }
            },
            "required": ["subject", "level", "question_type", "questions"]
        }
    }

@app.route('/generate-questions', methods=['POST'])
def generate_questions_api():
    if 'pdf_file' in request.files:
        pdf_file = request.files['pdf_file']
        
        # Check if the file is empty
        if pdf_file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Save the file temporarily to process
        pdf_file_path = 'temp.pdf'
        pdf_file.save(pdf_file_path)
        
        try:
            context = extract_text_from_pdf(pdf_file_path)
        except Exception as e:
            return jsonify({"error": f"Error reading PDF file: {str(e)}"}), 500
        
        os.remove(pdf_file_path)  # Clean up the file after processing
    elif 'text' in request.form:
        context = request.form['text']
    else:
        return jsonify({"error": "No PDF file or text provided."}), 400

    subject = request.form.get("subject")
    level = request.form.get("level")
    num_questions = int(request.form.get("num_questions", 1))
    question_type = request.form.get("question_type", "multiple_choice")

    if not subject or not level:
        return jsonify({"error": "Subject and education level must be provided."}), 400

    try:
        # Generate prompt with extracted text or provided text
        prompt = generate_prompt(subject, level, num_questions, question_type, context)

        # Generate questions using OpenAI
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert Indonesian exam question generator, fluent in Bahasa Indonesia and familiar with the Indonesian education system."},
                {"role": "user", "content": prompt}
            ],
            functions=[define_function(question_type)],
            function_call={"name": "generate_exam_questions"}
        )

        function_args = json.loads(response.choices[0].message.function_call.arguments)
        return jsonify(function_args)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
