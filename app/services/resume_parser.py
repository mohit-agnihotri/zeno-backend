from pypdf import PdfReader
import json
import httpx
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
    """Sends extracted text to local Ollama (Phi-3) to extract structured JSON."""
    
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

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json" # Ollama supports JSON mode natively
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            
            data = response.json()
            response_text = data.get("response", "{}")
            
            # Parse the JSON returned by Phi-3
            parsed_data = json.loads(response_text)
            
            return ParsedResume(**parsed_data)
            
    except Exception as e:
        print(f"Ollama AI Error: {e}")
        return None
