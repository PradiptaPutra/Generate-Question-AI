from flask import Flask, request, jsonify
from groq import Groq
import json

app = Flask(__name__)

client = Groq()
MODEL = 'llama3-groq-70b-8192-tool-use-preview'
MAX_ATTEMPTS = 3  # Maximum number of attempts for validation

def generate_improved_prompt(subject, level, num_questions, question_type):
    base_prompt = f"""Anda adalah seorang ahli pendidikan dan pembuat soal ujian profesional dengan pengalaman bertahun-tahun dalam mata pelajaran {subject} untuk tingkat {level}. Tugas Anda adalah membuat {num_questions} soal ujian berkualitas tinggi dalam Bahasa Indonesia.

Panduan umum:
1. Pastikan setiap soal sesuai dengan kurikulum dan standar kompetensi untuk {subject} tingkat {level}.
2. Gunakan bahasa yang jelas, ringkas, dan sesuai dengan tingkat pemahaman siswa.
3. Hindari ambiguitas atau kesalahan faktual dalam soal dan jawaban.
4. Pastikan soal mengukur pemahaman konseptual, bukan hanya ingatan faktual.
5. Variasikan tingkat kesulitan soal (mudah, sedang, sulit) secara proporsional.
6. Pastikan kunci jawaban benar-benar tepat dan dapat dipertanggungjawabkan.

"""

    if question_type == "pilihan ganda":
        specific_prompt = """Format untuk setiap soal pilihan ganda:
Pertanyaan [nomor]: [Isi pertanyaan]
A. [Pilihan A]
B. [Pilihan B]
C. [Pilihan C]
D. [Pilihan D]
Jawaban: [Huruf jawaban yang benar]
Penjelasan: [Penjelasan singkat mengapa jawaban tersebut benar]

Panduan khusus pilihan ganda:
1. Pastikan hanya ada satu jawaban yang benar.
2. Buat pengecoh (distractor) yang masuk akal tetapi jelas salah.
3. Hindari penggunaan "semua di atas benar" atau "tidak ada yang benar".
4. Pastikan panjang dan kompleksitas setiap pilihan jawaban relatif setara.
"""
    elif question_type == "essay":
        specific_prompt = """Format untuk setiap soal essay:
Pertanyaan [nomor]: [Isi pertanyaan]
Jawaban: [Poin-poin kunci yang harus ada dalam jawaban]
Rubrik Penilaian: [Kriteria penilaian jawaban, misalnya berdasarkan kelengkapan, kedalaman analisis, dll.]

Panduan khusus essay:
1. Buat pertanyaan yang mendorong pemikiran kritis dan analisis.
2. Sertakan poin-poin kunci yang diharapkan muncul dalam jawaban siswa.
3. Berikan rubrik penilaian yang jelas untuk membantu konsistensi dalam penilaian.
"""
    else:
        return "Error: Jenis soal tidak dikenal."

    final_prompt = base_prompt + specific_prompt + f"\nBuatlah {num_questions} soal {question_type} untuk mata pelajaran {subject} tingkat {level} sesuai dengan panduan di atas."
    return final_prompt

def parse_and_format_questions(validated_questions_text, question_type):
    questions = []
    individual_questions = validated_questions_text.split("\n\n")
    
    for q in individual_questions:
        lines = q.split("\n")
        question = next((line.split(": ", 1)[1] for line in lines if line.startswith("Pertanyaan")), "")
        
        if question_type == "pilihan ganda":
            answers = [line.split(". ", 1)[1] for line in lines if line[0].isalpha() and line[1] == "."]
            correct_answer = next((line.split(": ", 1)[1] for line in lines if line.startswith("Jawaban: ")), "").strip()
            explanation = next((line.split(": ", 1)[1] for line in lines if line.startswith("Penjelasan: ")), "")
            
            formatted_answers = [
                {
                    "text": answer,
                    "isCorrect": (chr(65 + i) == correct_answer)
                } for i, answer in enumerate(answers)
            ]
            
            questions.append({
                "question": question,
                "answers": formatted_answers,
                "explanation": explanation
            })
        elif question_type == "essay":
            answer = next((line.split(": ", 1)[1] for line in lines if line.startswith("Jawaban: ")), "")
            rubric = next((line.split(": ", 1)[1] for line in lines if line.startswith("Rubrik Penilaian: ")), "")
            questions.append({
                "question": question,
                "answer": answer,
                "rubric": rubric
            })
    
    return questions

def generate_and_validate_questions(subject, level, num_questions, question_type):
    """Generate and validate multiple exam questions and answers in Indonesian."""
    
    # Step 1: Generate initial questions and answers
    prompt_generate = generate_improved_prompt(subject, level, num_questions, question_type)
    
    messages_generate = [
        {"role": "system", "content": "Anda adalah asisten yang menghasilkan soal ujian berkualitas tinggi."},
        {"role": "user", "content": prompt_generate},
    ]
    
    response_generate = client.chat.completions.create(
        model=MODEL,
        messages=messages_generate,
        max_tokens=1000,
        temperature=0.7
    )
    
    questions_text = response_generate.choices[0].message.content.strip()
    
    # Step 2: Validate the generated results
    prompt_validate = (
        f"Berikut adalah {num_questions} soal dan jawabannya: \n\n{questions_text}\n\n"
        "Tolong periksa dengan sangat teliti apakah semua soal dan jawabannya sudah benar, sesuai, dan mengikuti format yang diminta. "
        "Pastikan bahwa:\n"
        "1. Setiap soal sesuai dengan tingkat pendidikan dan mata pelajaran yang diminta.\n"
        "2. Tidak ada kesalahan faktual atau konseptual dalam soal maupun jawaban.\n"
        "3. Format soal dan jawaban konsisten dan sesuai dengan yang diminta.\n"
        "4. Untuk soal pilihan ganda, pastikan hanya ada satu jawaban yang benar dan pengecoh masuk akal.\n"
        "5. Untuk soal essay, pastikan ada poin-poin kunci jawaban dan rubrik penilaian.\n"
        "Jika ada kesalahan atau ketidaksesuaian, perbaiki dengan hati-hati tanpa mengubah format aslinya. "
        "Jika sudah benar, kembalikan soal-soal tersebut tanpa perubahan. "
        "Pastikan output Anda tetap mengikuti format yang sama persis dengan input."
    )
    
    messages_validate = [
        {"role": "system", "content": "Anda adalah asisten yang memvalidasi soal ujian dengan sangat teliti."},
        {"role": "user", "content": prompt_validate},
    ]

    response_validate = client.chat.completions.create(
        model=MODEL,
        messages=messages_validate,
        max_tokens=1000,
        temperature=0.1
    )
    
    validated_questions_text = response_validate.choices[0].message.content.strip()
    
    # Step 3: Parse and format final output
    questions = parse_and_format_questions(validated_questions_text, question_type)
    
    return questions

@app.route('/generate-questions', methods=['POST'])
def generate_questions_api():
    data = request.json
    
    subject = data.get("subject")
    level = data.get("level")
    num_questions = int(data.get("num_questions", 1))
    question_type = data.get("question_type", "pilihan ganda")
    
    if not subject or not level:
        return jsonify({"error": "Subjek dan tingkat pendidikan harus disertakan."}), 400
    
    questions = generate_and_validate_questions(subject, level, num_questions, question_type)
    
    if isinstance(questions, dict) and "error" in questions:
        return jsonify({"error": questions["error"]}), 500
    
    return jsonify({
        "subject": subject,
        "level": level,
        "question_type": question_type,
        "questions": questions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)