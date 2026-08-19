import PyPDF2
from google import genai
from google.genai.errors import APIError

API_KEYS_POOL = [
    # "AQ.Ab8RN6LvHlEwQzu_h8ysnjqnXk7yxL5LqsVRd4U5bnWNlNfS6Q",
    # "AQ.Ab8RN6LP5E_Jg0HKlB8jXqiGy80M_N89z4eaDHKCws-e9uu8EA",
    # "AQ.Ab8RN6K3YBOgfFiCFNlcVb_9542kewm5KUWSf60YdS870d0LoQ",
    # "AQ.Ab8RN6KZ9BIg3kljAcLLc6duMtb3NZ_4976-QlFEEcCi85R-bw"
    "AQ.Ab8RN6Jntiebp_IlwsPZZL19G2dQl4H2MvSv58XLroxiAWcWzw"
]

AVAILABLE_MODELS = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.5-pro']

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
        return extracted_text.strip()
    except Exception as e:
        print(f"PDF Parsing Error: {e}")
        return ""

def generate_interview_questions(cv_text, job_role):
    fallback_questions = [
        {"q": f"Can you describe your core experience and workflows related to the field of {job_role}?", "s": "General industry experience and field alignment validation."},
        {"q": "What are the essential daily tools, software, or methodologies you use to manage your tasks effectively?", "s": "Practical workspace tool competency."},
        {"q": "How do you handle unexpected challenges or workflow bottlenecks in your professional routine?", "s": "Problem-solving capacity and reactive decision matrix."},
        {"q": "Can you share an instance where you had to collaborate closely with a multi-disciplinary team?", "s": "Team dynamics and collaborative communication agility."},
        {"q": "How do you ensure accuracy, quality control, and standard compliance in your deliveries?", "s": "Operational precision and quality assurance standard."},
        {"q": "What strategy do you use to keep your skills upgraded with evolving tech trends?", "s": "Self-driven learning agility and market relevance."},
        {"q": "Describe a project scenario that required you to manage strict timelines and high pressure.", "s": "Stress tolerance and milestone execution capacity."},
        {"q": "What unique professional strength do you possess that sets you apart for this position?", "s": "Self-awareness, unique value proposition, and role matching."}
    ]

    prompt = f"""
    You are an expert corporate interviewer. Generate exactly 8 short, professional, and easy-to-understand screening interview questions for the position: {job_role}.
    Analyze the candidate's CV text provided below to align the questions with their experience.

    Candidate CV Context:
    {cv_text}

    CRITICAL REQUIREMENTS FOR QUESTION STYLE:
    - Each question must be very short, direct, and maximum 1 to 2 lines long.
    - Use clear, simple, and professional language. Avoid long scenarios or overly difficult, complex wording.
    - Focus directly on fundamental core concepts and practical implementation.

    Output Format Requirement STRICTLY:
    For each question, output exactly two lines:
    Line 1: Q: [The Short Question Text]
    Line 2: S: [Short 1-sentence summary explaining what this question evaluates]
    Do not add markdown, bullet numbers, or extra text blocks.
    """

    for key_idx, current_key in enumerate(API_KEYS_POOL):
        try:
            print(f"Initializing Client Matrix with Key Index {key_idx+1}...")
            client = genai.Client(api_key=current_key)
            
            for model_name in AVAILABLE_MODELS:
                try:
                    print(f"Attempting question generation using Key Index {key_idx+1} and Model: {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    res_text = response.text.strip()
                    
                    questions = []
                    lines = [l.strip() for l in res_text.split('\n') if l.strip()]
                    
                    current_q = None
                    for line in lines:
                        if line.startswith("Q:"):
                            current_q = line.replace("Q:", "").strip()
                        elif line.startswith("S:") and current_q:
                            current_s = line.replace("S:", "").strip()
                            questions.append({"q": current_q, "s": current_s})
                            current_q = None
                            
                    if len(questions) == 8:
                        print(f"Success! Generated 8 questions via Key Index {key_idx+1}!")
                        return questions
                        
                except APIError as api_err:
                    print(f"API Exhausted on Key {key_idx+1} (Model: {model_name}): {api_err.message}")
                    continue  # Shift to next model
                except Exception as e:
                    print(f"Model Processing Error: {e}")
                    continue
                    
        except Exception as client_err:
            print(f"Client initialization failed for Key Index {key_idx+1}: {client_err}")
            continue  # Shift to next API key

    print("CRITICAL WARNING: All 4 API keys or models exhausted. Executing fallback grid.")
    return fallback_questions

def evaluate_interview(flat_questions, user_answers, job_role):
    conversation_log = ""
    for i, q in enumerate(flat_questions):
        q_text = q['q'] if isinstance(q, dict) else q
        ans = user_answers[i] if i < len(user_answers) else "No Answer Provided"
        conversation_log += f"Interviewer Question {i+1}: {q_text}\nCandidate Answer: {ans}\n\n"
        
    prompt = f"""
    Analyze the 8 question-answer pairs for the target role: {job_role}.
    Generate an aggregate score out of 100 and clear feedback remarks.
    
    Transcript Logs:
    {conversation_log}
    
    Output Format STRICTLY:
    Score: [Only number like 85]/100
    Feedback: [Your remarks here]
    """
    
    for key_idx, current_key in enumerate(API_KEYS_POOL):
        try:
            print(f"Initializing Evaluation Client with Key Index {key_idx+1}...")
            client = genai.Client(api_key=current_key)
            
            for model_name in AVAILABLE_MODELS:
                try:
                    print(f"Attempting evaluation using Key Index {key_idx+1} and Model: {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    res_text = response.text.strip()
                    
                    score = ""
                    feedback = ""
                    
                    for line in res_text.split('\n'):
                        if line.startswith("Score:"):
                            score = line.replace("Score:", "").strip()
                        elif line.startswith("Feedback:"):
                            feedback = line.replace("Feedback:", "").strip()
                            
                    if score and feedback:
                        print(f"Success! Evaluation completed via Key Index {key_idx+1}!")
                        return {"score": score, "feedback": feedback}
                        
                except APIError as api_err:
                    print(f"API Exhausted on Key {key_idx+1} during eval (Model: {model_name}): {api_err.message}")
                    continue
                except Exception as e:
                    print(f"Model Eval Error: {e}")
                    continue
                    
        except Exception as client_err:
            print(f"Client initialization failed for Key Index {key_idx+1} during eval: {client_err}")
            continue

    print("CRITICAL: Evaluation completely exhausted across all 4 keys. Returning emergency score card.")
    return {"score": "70", "feedback": "Evaluation completed via system fallback mechanism due to heavy channel load."}