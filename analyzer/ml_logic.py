import docx2txt
import PyPDF2
import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fpdf import FPDF
from sklearn.feature_extraction import text

# Remove emojis/unicode that fpdf can't handle
def remove_emojis(text):
    return text.encode('ascii', 'ignore').decode('ascii')

# Helper: extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text() or ''
    return text

# Helper: extract text from DOCX
def extract_text_from_docx(file):
    return docx2txt.process(file)

# Clean and preprocess text
def preprocess(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text

# Keyword extraction with stop word filtering
def extract_keywords(text_input):
    stop_words = set(text.ENGLISH_STOP_WORDS)
    words = preprocess(text_input).split()
    keywords = set(word for word in words if word not in stop_words and len(word) > 1)
    return keywords

# Feedback generator based on score and keywords
def get_feedback(score, missing_keywords):
    suggestions = []
    top_missing = list(missing_keywords)[:10]

    if any(word in top_missing for word in ["team", "collaboration", "agile"]):
        suggestions.append(" Highlight teamwork or Agile collaboration experience.")
    if any(word in top_missing for word in ["api", "rest", "endpoint"]):
        suggestions.append(" Mention REST API or web service experience.")
    if any(word in top_missing for word in ["docker", "ci", "cd", "deployment"]):
        suggestions.append(" Add experience with Docker, CI/CD or deployment tools.")
    if any(word in top_missing for word in ["tensorflow", "keras", "nlp"]):
        suggestions.append(" Mention specific AI/ML frameworks like TensorFlow, Keras or NLP.")
    if any(word in top_missing for word in ["communication", "leadership"]):
        suggestions.append(" Add soft skills like communication and leadership.")

    if score >= 75:
        summary = "✅ Excellent match. Your resume is strong and ready to apply!"
    elif score >= 50:
        summary = "⚠️ Fair match. Improve by adding more job-specific keywords."
    else:
        summary = "❌ Weak match. Tailor your resume to align better with the job description."

    return summary, suggestions

# Main analysis function
def analyze_resume_ats(resume_file, jd_text):
    if resume_file.name.endswith(".pdf"):
        resume_text = extract_text_from_pdf(resume_file)
    else:
        resume_text = extract_text_from_docx(resume_file)

    resume_text = preprocess(resume_text)
    jd_text = preprocess(jd_text)

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_text, jd_text])
    score = round(cosine_similarity(vectors[0:1], vectors[1:2])[0][0] * 100)

    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)
    matched = sorted(resume_keywords & jd_keywords)
    missing = sorted(jd_keywords - resume_keywords)

    summary, suggestions = get_feedback(score, missing)

    return {
        "score": score,
        "matched": matched,
        "missing": missing[:10],
        "summary": summary,
        "suggestions": suggestions,
        "job_description": jd_text[:300] + "..."
    }

# Export result to PDF (without emojis)
def generate_feedback_pdf(result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "MatchMyResume - Resume Report", ln=True)
    pdf.ln(10)

    pdf.cell(0, 10, f"Match Score: {result['score']}%", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "Summary:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, remove_emojis(result['summary']))

    if result['suggestions']:
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, "Suggestions:", ln=True)
        pdf.set_font("Arial", size=12)
        for suggestion in result['suggestions']:
            pdf.multi_cell(0, 10, f"- {remove_emojis(suggestion)}")

    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "Matched Keywords:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, remove_emojis(", ".join(result['matched'])))

    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "Missing Keywords:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, remove_emojis(", ".join(result['missing'])))

    return pdf
