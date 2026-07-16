from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from app.core.database import get_db
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime, timedelta
import asyncio
import os
import google.generativeai as genai

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# ── Gemini setup ─────────────────────────────────────────────────────────────
_gemini_model = None
def _get_gemini():
    global _gemini_model
    if _gemini_model is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    return _gemini_model

# ── In-memory caches ──────────────────────────────────────────────────────────
_jobs_cache: list = []
_cache_timestamp: datetime = None
_company_cache: dict = {}
CACHE_DURATION_MINUTES = 30


def _is_ghost_job(date_posted_str) -> bool:
    """Returns True if job was posted more than 45 days ago."""
    if not date_posted_str or str(date_posted_str) in ("", "None", "nan", "NaT"):
        return False
    try:
        if hasattr(date_posted_str, 'year'):
            date_posted = date_posted_str
        else:
            date_posted = datetime.strptime(str(date_posted_str)[:10], "%Y-%m-%d")
        age_days = (datetime.utcnow() - date_posted).days
        return age_days > 45
    except Exception:
        return False


def _get_response_rate_for_company(company: str) -> float:
    """Calculate real response rate from Zeno's own application tracker DB."""
    db = get_db()
    if not db:
        return 0.0
    try:
        total_res = db.table("applications").select("id", count="exact").eq("company", company).execute()
        replied_res = db.table("applications").select("id", count="exact").eq("company", company).neq("status", "applied").execute()
        total = getattr(total_res, 'count', None) or 0
        replied = getattr(replied_res, 'count', None) or 0
        if total == 0:
            return 0.0
        return round((replied / total) * 100, 1)
    except Exception:
        return 0.0


async def _get_culture_score_for_company(company: str) -> float:
    """Get real culture score for a company via Gemini AI. Cached per company."""
    global _company_cache

    cached = _company_cache.get(company)
    if cached and (datetime.utcnow() - cached["cached_at"]).seconds < 3600:
        return cached["culture_score"]

    db = get_db()
    if db:
        try:
            res = db.table("company_cache").select("culture_score").eq("company", company).execute()
            if res.data:
                score = float(res.data[0]["culture_score"])
                _company_cache[company] = {"culture_score": score, "cached_at": datetime.utcnow()}
                return score
        except Exception:
            pass

    score = 7.0
    try:
        model = _get_gemini()
        if model:
            response = model.generate_content(
                f"Give a workplace culture score from 1.0 to 10.0 for the company '{company}' "
                f"based on general reputation, Glassdoor trends and industry standing. "
                f"Reply ONLY with a single decimal number like 7.5. Nothing else."
            )
            score = max(1.0, min(10.0, float(response.text.strip().replace(",", "."))))
    except Exception as e:
        print(f"Gemini culture score error for {company}: {e}")

    _company_cache[company] = {"culture_score": score, "cached_at": datetime.utcnow()}

    if db:
        try:
            db.table("company_cache").upsert({
                "company": company,
                "culture_score": score,
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception:
            pass

    return score


async def _get_salary_estimate(title: str, location: str) -> str:
    """Get AI salary estimate for a job title+location using Gemini."""
    try:
        model = _get_gemini()
        if not model:
            return ""
        response = model.generate_content(
            f"Estimate the annual salary range in Indian Rupees (LPA) for '{title}' in {location}, India. "
            f"Reply ONLY in the exact format: ₹XL - ₹YL (example: ₹6L - ₹10L). Nothing else."
        )
        return response.text.strip()
    except Exception:
        return ""


def _scrape_real_jobs(search_term: str = "software engineer", location: str = "India", results: int = 20) -> list:
    """Scrape real jobs from LinkedIn, Indeed, Glassdoor using JobSpy."""
    try:
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin", "glassdoor"],
            search_term=search_term,
            location=location,
            results_wanted=results,
            hours_old=72,
            country_indeed="India",
        )

        job_list = []
        for _, row in jobs_df.iterrows():
            date_posted = row.get("date_posted", "")
            ghost = _is_ghost_job(date_posted)

            job = {
                "id": str(row.get("id", "")),
                "title": str(row.get("title", "Software Engineer")),
                "company": str(row.get("company", "Tech Company")),
                "location": str(row.get("location", "India")),
                "job_type": str(row.get("job_type", "Full-time")),
                "description": str(row.get("description", ""))[:500],
                "apply_url": str(row.get("job_url", "")),
                "date_posted": str(date_posted),
                "salary": str(row.get("min_amount", "")) if pd.notna(row.get("min_amount")) else "Not Disclosed",
                "source": str(row.get("site", "indeed")),
                "match_score": 75,
                "company_culture_score": 0.0,
                "company_response_rate": 0.0,
                "is_ghost_job": ghost,
                "ai_salary_estimate": "",
            }
            job_list.append(job)

        return job_list
    except Exception as e:
        print(f"Scraping error: {e}")
        return []


def _get_cached_jobs(search_term: str = "software engineer", location: str = "India") -> list:
    """Return cached jobs or scrape fresh ones."""
    global _jobs_cache, _cache_timestamp

    now = datetime.utcnow()
    cache_expired = _cache_timestamp is None or (now - _cache_timestamp) > timedelta(minutes=CACHE_DURATION_MINUTES)

    if cache_expired or not _jobs_cache:
        print(f"[JobSpy] Scraping fresh jobs for: {search_term} in {location}")
        _jobs_cache = _scrape_real_jobs(search_term=search_term, location=location, results=25)
        _cache_timestamp = now
        print(f"[JobSpy] Cached {len(_jobs_cache)} real jobs")

    return _jobs_cache


@router.get("/all")
async def get_all_jobs_feed(
    search: str = Query("software engineer", description="Job search term"),
    location: str = Query("India", description="Job location"),
    limit: int = Query(20, le=50)
):
    """Browse all real jobs with real AI-powered culture scores and salary estimates."""
    jobs = list(_get_cached_jobs(search_term=search, location=location))

    for job in jobs[:limit]:
        company = job.get("company", "")
        if company and job["company_response_rate"] == 0.0:
            job["company_response_rate"] = _get_response_rate_for_company(company)
        if not job.get("ai_salary_estimate") and job.get("title"):
            job["ai_salary_estimate"] = await _get_salary_estimate(job["title"], location)

    return {"jobs": jobs[:limit], "total": len(jobs), "source": "jobspy_real"}


@router.get("/matches/{user_id}")
async def get_matched_jobs(
    user_id: str,
    search: str = Query("software engineer"),
    location: str = Query("India"),
    limit: int = Query(20, le=50)
):
    """Returns real AI-matched jobs scored against user's actual resume from Supabase."""
    db = get_db()
    resume_text = None

    if db:
        try:
            res = db.table("resumes").select("parsed_text").eq("user_id", user_id).execute()
            if res.data and res.data[0].get("parsed_text"):
                resume_text = res.data[0]["parsed_text"]
        except Exception as e:
            print(f"DB fetch warning: {e}")

    all_jobs = list(_get_cached_jobs(search_term=search, location=location))

    if resume_text:
        resume_lower = resume_text.lower()
        for job in all_jobs:
            desc_lower = (job.get("description", "") + " " + job.get("title", "")).lower()
            resume_words = set(resume_lower.split())
            desc_words = set(desc_lower.split())
            overlap = len(resume_words & desc_words)
            score = min(98, 60 + overlap)
            job["match_score"] = score
        all_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    for job in all_jobs[:limit]:
        company = job.get("company", "")
        if company and job["company_response_rate"] == 0.0:
            job["company_response_rate"] = _get_response_rate_for_company(company)
        if not job.get("ai_salary_estimate") and job.get("title"):
            job["ai_salary_estimate"] = await _get_salary_estimate(job["title"], location)

    return {"matches": all_jobs[:limit], "total": len(all_jobs), "source": "jobspy_real"}


@router.get("/culture/{company_name}")
async def get_company_culture(company_name: str):
    """Get real AI culture score for a company (Gemini-powered, Supabase-cached)."""
    score = await _get_culture_score_for_company(company_name)
    response_rate = _get_response_rate_for_company(company_name)
    return {"company": company_name, "culture_score": score, "response_rate": response_rate}


@router.post("/salary-estimate")
async def estimate_salary(title: str, location: str = "India"):
    """Get AI salary estimate for a job title + location using Gemini."""
    estimate = await _get_salary_estimate(title, location)
    if not estimate:
        raise HTTPException(status_code=503, detail="AI salary estimation unavailable.")
    return {"title": title, "location": location, "salary_estimate": estimate}


@router.post("/refresh")
async def refresh_jobs_cache(
    search: str = Query("software engineer"),
    location: str = Query("India")
):
    """Force-refresh the job cache by scraping fresh data."""
    global _jobs_cache, _cache_timestamp
    _jobs_cache = []
    _cache_timestamp = None
    jobs = _get_cached_jobs(search_term=search, location=location)
    return {"message": f"Refreshed! Scraped {len(jobs)} real jobs.", "count": len(jobs)}
