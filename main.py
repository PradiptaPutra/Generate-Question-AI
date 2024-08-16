from flask import Flask, request, jsonify
from groq import Groq
import json

app = Flask(__name__)

client = Groq()
MODEL = 'llama3-groq-70b-8192-tool-use-preview'
MAX_ATTEMPTS = 3  # Batas maksimal percobaan untuk validasi

def generate_and_validate_question(subject, level, question_type):
    """Generate and validate a single exam question and answers in Indonesian."""
    
    for attempt in range(MAX_ATTEMPTS):
        # Langkah 1: Generate pertanyaan dan jawaban awal
        if question_type == "pilihan ganda":
            prompt_generate = (
                f"Buatkan satu soal ujian tingkat {level} untuk mata pelajaran {subject} dalam Bahasa Indonesia, "
                "dalam bentuk pilihan ganda dengan 4 pilihan jawaban. Tandai jawaban yang benar dengan asterisk (*) dan pastikan soalnya benar dan sesuai."
            )
        elif question_type == "essay":
            prompt_generate = (
                f"Buatkan satu soal ujian tingkat {level} untuk mata pelajaran {subject} dalam Bahasa Indonesia, "
                "dalam bentuk soal essay yang membutuhkan jawaban singkat."
            )
        else:
            return {"error": f"Jenis soal '{question_type}' tidak dikenal. Pilih dari: 'pilihan ganda' atau 'essay'."}
        
        messages_generate = [
            {"role": "system", "content": "Anda adalah asisten yang menghasilkan soal ujian."},
            {"role": "user", "content": prompt_generate},
        ]
        
        response_generate = client.chat.completions.create(
            model=MODEL,
            messages=messages_generate,
            max_tokens=300,
            temperature=0.7
        )
        
        question_text = response_generate.choices[0].message.content.strip()
        
        # Langkah 2: Validasi hasil yang dihasilkan
        prompt_validate = (
            f"Berikut adalah soal dan jawabannya: \n\n{question_text}\n\n"
            "Tolong periksa apakah soal dan jawabannya sudah benar dan sesuai. "
            "Jika ada kesalahan atau ketidaksesuaian, jelaskan. Jika sudah benar, konfirmasi bahwa ini sudah sesuai."
        )
        
        messages_validate = [
            {"role": "system", "content": "Anda adalah asisten yang memvalidasi soal ujian."},
            {"role": "user", "content": prompt_validate},
        ]
        
        response_validate = client.chat.completions.create(
            model=MODEL,
            messages=messages_validate,
            max_tokens=300,
            temperature=0.7
        )
        
        validation_text = response_validate.choices[0].message.content.strip()
        
        # Langkah 3: Analisis hasil validasi dan output final
        if "sudah sesuai" in validation_text.lower() or "benar" in validation_text.lower():
            if question_type == "pilihan ganda":
                lines = question_text.split("\n")
                question = lines[0].strip()
                answers = [line.strip() for line in lines[1:] if line.strip()]
                
                formatted_answers = []
                for answer in answers:
                    is_correct = "*" in answer
                    formatted_answer = {
                        "text": answer.replace("*", "").strip(),
                        "Jawaban": is_correct
                    }
                    formatted_answers.append(formatted_answer)
                
                return {
                    "question": question,
                    "answers": formatted_answers,
                    "attempts": attempt + 1
                }
            elif question_type == "essay":
                return {
                    "question": question_text,
                    "answers": [],  # Soal essay tidak memerlukan pilihan jawaban
                    "attempts": attempt + 1
                }
    
    # Jika masih tidak valid setelah MAX_ATTEMPTS
    return {"error": "Soal yang dihasilkan tidak valid setelah beberapa kali percobaan. Silakan coba lagi."}

@app.route('/generate-question', methods=['POST'])
def generate_question_api():
    data = request.json
    
    subject = data.get("subject")
    level = data.get("level")
    num_questions = data.get("num_questions", 1)  # Jumlah soal yang ingin dihasilkan
    question_type = data.get("question_type", "pilihan ganda")  # Jenis soal: 'essay' atau 'pilihan ganda'
    
    if not subject or not level:
        return jsonify({"error": "Subjek dan tingkat pendidikan harus disertakan."}), 400
    
    questions = []
    for _ in range(num_questions):
        question = generate_and_validate_question(subject, level, question_type)
        if "error" in question:
            return jsonify({"error": question["error"]}), 500
        questions.append(question)
    
    return jsonify({
        "subject": subject,
        "level": level,
        "questions": questions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
