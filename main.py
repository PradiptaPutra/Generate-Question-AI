from flask import Flask, request, jsonify
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import json
import os

app = Flask(__name__)

# Set your OpenAI API key
MODEL = "gpt-4o-mini"  # Or another suitable model that supports function calling

def generate_prompt(subject: str, level: str, num_questions: int, question_type: str) -> str:
    return f"""Create {num_questions} high-quality {question_type} questions in Bahasa Indonesia for a {subject} exam at the {level} level for Indonesian students. 
    Consider the following guidelines:
    1. Ensure the questions are aligned with the Indonesian national curriculum (Kurikulum Nasional).
    2. Use contexts, examples, and scenarios that are familiar to Indonesian students.
    3. Include references to Indonesian culture, geography, history, or daily life where appropriate.
    4. Ensure language use is appropriate for the specified education level in Indonesia.
    5. For multiple-choice questions, provide 4 options (A, B, C, D).
    6. Provide detailed explanations or rubrics in Bahasa Indonesia.
    7. Use the appropriate terminology for the subject as it would be taught in Indonesian schools."""

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
    data = request.json
    subject = data.get("subject")
    level = data.get("level")
    num_questions = int(data.get("num_questions", 1))
    question_type = data.get("question_type", "multiple_choice")

    if not subject or not level:
        return jsonify({"error": "Subject and education level must be provided."}), 400

    prompt = generate_prompt(subject, level, num_questions, question_type)

    try:
        response = client.chat.completions.create(model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert Indonesian exam question generator, fluent in Bahasa Indonesia and familiar with the Indonesian education system."},
            {"role": "user", "content": prompt}
        ],
        functions=[define_function(question_type)],
        function_call={"name": "generate_exam_questions"})

        function_args = json.loads(response.choices[0].message.function_call.arguments)
        return jsonify(function_args)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
