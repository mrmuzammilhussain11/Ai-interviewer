import time
from flask import Flask, render_template, request, redirect, url_for
from ai_logic import extract_text_from_pdf, generate_interview_questions, evaluate_interview

app = Flask(__name__)

session_data = {
    "job_role": "",
    "questions": [],      
    "current_index": 0,
    "user_answers": [],
    "durations": []       
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/interview', methods=['POST'])
def start_interview():
    global session_data
    job_role = request.form.get('job_role')
    cv_file = request.files.get('cv')
    
    if cv_file and cv_file.filename != '':
        cv_text = extract_text_from_pdf(cv_file)
        ai_questions = generate_interview_questions(cv_text, job_role)
        
        session_data["job_role"] = job_role
        session_data["questions"] = ai_questions
        session_data["current_index"] = 0
        session_data["user_answers"] = []
        session_data["durations"] = []  
        
        first_item = ai_questions[0]
        return render_template('interview.html', 
                            job_role=job_role, 
                            question=first_item["q"],
                            summary=first_item["s"],
                            questions_list=ai_questions, 
                            current_idx=0,
                            durations=session_data["durations"])
    return redirect(url_for('index'))

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    global session_data
    user_answer = request.form.get('user_answer', '')
    time_taken = request.form.get('time_taken', '0')
    
    session_data["user_answers"].append(user_answer)
    session_data["durations"].append(time_taken)       
    
    current_idx = session_data["current_index"]
    session_data["current_index"] += 1
    next_idx = session_data["current_index"]
    
    if next_idx < len(session_data["questions"]):
        next_item = session_data["questions"][next_idx]
        return render_template('interview.html', 
                            job_role=session_data["job_role"], 
                            question=next_item["q"],
                            summary=next_item["s"],
                            questions_list=session_data["questions"], 
                            current_idx=next_idx,
                            durations=session_data["durations"])
    
    flat_questions_list = [item["q"] for item in session_data["questions"]]
    report = evaluate_interview(
        flat_questions_list, 
        session_data["user_answers"], 
        session_data["job_role"]
    )
    
    return render_template('report.html', 
                            job_role=session_data["job_role"], 
                            score=report["score"], 
                            feedback=report["feedback"])

if __name__ == '__main__':
    app.run(debug=True)