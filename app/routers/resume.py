from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.resume_parser import extract_text_from_pdf, parse_resume_with_ai
from app.services.ats_checker import calculate_ats_score
from app.core.database import get_db
import tempfile
import os
import json
import google.generativeai as genai
from pydantic import BaseModel

class XRayRequest(BaseModel):
    resume_text: str
    job_description: str

router = APIRouter(prefix="/resume", tags=["Resume"])

@router.post("/upload")
async def upload_and_parse_resume(user_id: str, file: UploadFile = File(...)):
    """
    Upload a PDF resume → parse → score local jobs → save to Supabase (if connected).
    Returns: parsed data + ATS score + top matched jobs
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        # 1. Save PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # 2. Extract text
        raw_text = extract_text_from_pdf(tmp_path)
        os.unlink(tmp_path)

        if not raw_text or len(raw_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. It might be image-based.")

        # 3. Calculate ATS Score (rule-based, no AI needed)
        ats_result = calculate_ats_score(raw_text, [])

        # 4. Return empty matches (Android client will automatically fallback to /jobs/matches API)
        matched_jobs = []

        # 5. Try AI parsing (optional — needs Ollama running)
        parsed_data = None
        try:
            parsed_data = await parse_resume_with_ai(raw_text)
        except Exception:
            pass  # Ollama not running — that's OK

        # 6. Save to Supabase (if connected)
        db = get_db()
        if db:
            try:
                db.table("resumes").upsert({
                    "user_id": user_id,
                    "parsed_text": raw_text,
                    "ats_score": ats_result.score,
                    "resume_vector": [],
                    "parsed_skills": parsed_data.skills if parsed_data else [],
                }).execute()

                if parsed_data and parsed_data.college:
                    db.table("users").update({
                        "college": parsed_data.college,
                        "graduation_year": parsed_data.graduation_year
                    }).eq("id", user_id).execute()
            except Exception as db_err:
                print(f"Supabase save error (non-fatal): {db_err}")

        return {
            "message": "Resume parsed successfully.",
            "ats_score": ats_result.score,
            "ats_feedback": ats_result.feedback,
            "parsed_data": parsed_data.model_dump() if parsed_data else {"skills": []},
            "matches": matched_jobs,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@router.post("/roast")
async def roast_resume(user_id: str, file: UploadFile = File(...)):
    """
    Fun but honest AI resume roast.
    Returns sarcastic + constructive feedback based on resume content.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        raw_text = extract_text_from_pdf(tmp_path)
        os.unlink(tmp_path)

        if not raw_text:
            raise HTTPException(status_code=400, detail="Could not read PDF.")

        roast_lines = _generate_roast(raw_text)
        return {"roast": roast_lines}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_roast(text: str) -> list:
    """Smart rule-based resume roast generator."""
    text_lower = text.lower()
    roast = []

    # Objective section check
    if "objective" in text_lower:
        roast.append("🔥 You still have an 'Objective' section? Bold move. Recruiters haven't read those since 2010.")
    
    # "Hardworking" buzzwords
    if any(w in text_lower for w in ["hardworking", "team player", "passionate", "quick learner"]):
        roast.append("😬 'Hardworking team player'? Congratulations, you're indistinguishable from 10,000 other resumes.")
    
    # Multiple pages
    if len(text) > 3000:
        roast.append("📜 Your resume is longer than my attention span. And I'm an AI. Cut it to 1 page.")
    
    # No numbers/metrics
    if not any(c.isdigit() for c in text):
        roast.append("📊 Not a single number in your entire resume. 'Improved performance' by HOW MUCH? 0.01% is still an improvement.")
    
    # Skills section keywords
    if "ms office" in text_lower or "microsoft office" in text_lower:
        roast.append("💾 You listed MS Office as a skill. So did every 45-year-old in the company. Next.")
    
    # GitHub check
    if "github" not in text_lower and "portfolio" not in text_lower:
        roast.append("👾 No GitHub link? Are your projects shy? Put them online, they won't bite.")
    
    # Email check
    if any(name in text_lower for name in ["cute", "cool", "swag", "gamer", "king", "queen", "boss"]):
        roast.append("📧 That email address tells me everything I need to know about your college years.")
    
    # Positive note at the end
    roast.append("✨ All jokes aside, you're applying which is more than most people do. Polish these points and you'll genuinely stand out!")
    
    if not roast or len(roast) < 2:
        roast = [
            "🤔 Your resume is... fine. Dangerously average. Like a plain paratha — no butter, no achaar.",
            "🎯 Add more quantifiable achievements. Numbers make recruiters' eyes light up.",
            "🔗 Add a GitHub profile with at least 3 pinned projects.",
            "✨ But hey — you're putting yourself out there. That already makes you better than 70% who only think about applying!"
        ]
    
    return roast

@router.post("/ats-xray")
async def ats_xray(request: XRayRequest):
    """
    Use Gemini AI to compare resume text against a job description.
    Returns matched keywords and missing keywords for ATS optimization.
    """
    if not request.resume_text or not request.job_description:
        raise HTTPException(status_code=400, detail="Missing resume or job description.")
        
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            # Fallback mock if no API key
            return {
                "matched_keywords": ["REST API", "Agile", "Kotlin", "Android"],
                "missing_keywords": ["CI/CD", "GraphQL", "Jetpack Compose"]
            }
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        Act as an ATS (Applicant Tracking System) expert. 
        Compare the following Resume against the Job Description.
        Extract up to 10 hard technical skills (keywords) from the Job Description.
        Determine which of those keywords exist in the Resume (matched_keywords) and which do not (missing_keywords).
        
        Reply ONLY with valid JSON in this exact format, with no markdown formatting or code blocks:
        {{
            "matched_keywords": ["keyword1", "keyword2"],
            "missing_keywords": ["keyword3", "keyword4"]
        }}
        
        Resume:
        {request.resume_text}
        
        Job Description:
        {request.job_description}
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean up if model added markdown ```json
        if text.startswith("```json"):
            text = text.replace("```json", "", 1)
        if text.endswith("```"):
            text = text[:-3]
            
        result = json.loads(text.strip())
        return result
        
    except Exception as e:
        print(f"ATS X-Ray error: {e}")
        # Return fallback on error so UI doesn't break
        return {
            "matched_keywords": ["Software", "Development"],
            "missing_keywords": ["Specific Skill 1", "Specific Skill 2"]
        }
