from pypdf import PdfReader
import json
import httpx
import os
import google.generativeai as genai
from typing import Optional
from app.schemas.resume import ParsedResume

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3" # Local Phi-3 model

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts raw text from a PDF file using pypdf."""
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text.strip()


async def parse_resume_with_ai(resume_text: str) -> Optional[ParsedResume]:
    """Sends extracted text to Gemini to extract structured JSON."""
    
    prompt = f"""
    You are an expert ATS (Applicant Tracking System). Extract the following information from the resume text provided below.
    Return ONLY a raw JSON object (no markdown, no backticks, no explanations) matching this structure:
    {{
      "name": "Full Name",
      "email": "Email Address",
      "phone": "Phone Number",
      "skills": ["Skill 1", "Skill 2"],
      "college": "University Name",
      "graduation_year": 2024,
      "projects": ["Project 1 name/desc", "Project 2"],
      "experience": ["Exp 1", "Exp 2"]
    }}

    Resume Text:
    {resume_text}
    """

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        ai_resp = model.generate_content(prompt)
        
        raw_text = ai_resp.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        json_data = json.loads(raw_text)
        return ParsedResume(**json_data)
        
    except Exception as e:
        print(f"Error parsing resume with Gemini: {e}")
        return None
