import re
from typing import List
from app.schemas.resume import ATSScoreResponse

def calculate_ats_score(resume_text: str, parsed_skills: List[str]) -> ATSScoreResponse:
    """
    Rule-based True ATS Score checker (0 LLM cost).
    Checks for common ATS formatting issues, keyword density, and essential sections.
    """
    score = 100
    feedback = []
    
    text_lower = resume_text.lower()
    
    # 1. Contact Info Check
    if not re.search(r'[\w\.-]+@[\w\.-]+', text_lower):
        score -= 15
        feedback.append("Missing or unreadable email address.")
        
    if not re.search(r'\+?\d{10,14}', text_lower):
        score -= 10
        feedback.append("Missing or unreadable phone number.")
        
    # 2. LinkedIn / GitHub links
    if 'linkedin.com' not in text_lower:
        score -= 10
        feedback.append("Consider adding your LinkedIn profile URL.")
        
    if 'github.com' not in text_lower:
        score -= 5
        feedback.append("Adding a GitHub URL increases technical profile strength.")

    # 3. Standard Section Headers Check
    essential_sections = ['experience', 'education', 'skills', 'projects']
    for section in essential_sections:
        if section not in text_lower:
            score -= 5
            feedback.append(f"Missing standard section header: '{section.capitalize()}'. ATS might not parse this correctly.")

    # 4. Action Verbs Check
    action_verbs = ['developed', 'created', 'designed', 'managed', 'implemented', 'built', 'led', 'analyzed']
    verb_count = sum(1 for verb in action_verbs if verb in text_lower)
    if verb_count < 3:
        score -= 10
        feedback.append("Low usage of action verbs. Start bullet points with strong verbs (e.g., Developed, Designed).")

    # 5. Length Check
    word_count = len(resume_text.split())
    if word_count < 200:
        score -= 15
        feedback.append("Resume is too short. Provide more details about your projects and impact.")
    elif word_count > 1000:
        score -= 10
        feedback.append("Resume is too long. Try to keep it concise and under 2 pages max.")

    # Ensure score doesn't go below 0
    score = max(0, score)

    return ATSScoreResponse(
        score=score,
        feedback=feedback,
        missing_keywords=[] # This will be populated later when comparing against a specific job
    )
