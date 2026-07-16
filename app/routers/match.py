from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from app.core.database import get_db
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime, timedelta
import asyncio

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Simple in-memory cache to avoid hammering scrapers on every request
_jobs_cache: list = []
_cache_timestamp: datetime = None
CACHE_DURATION_MINUTES = 30  # Re-scrape every 30 minutes

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
            job = {
                "id": str(row.get("id", "")),
                "title": str(row.get("title", "Software Engineer")),
                "company": str(row.get("company", "Tech Company")),
                "location": str(row.get("location", "India")),
                "job_type": str(row.get("job_type", "Full-time")),
                "description": str(row.get("description", ""))[:500],
                "apply_url": str(row.get("job_url", "")),
                "date_posted": str(row.get("date_posted", "")),
                "salary": str(row.get("min_amount", "")) if pd.notna(row.get("min_amount")) else "Not Disclosed",
                "source": str(row.get("site", "indeed")),
                "match_score": 75,  # Default, updated by matching algorithm
                "company_culture_score": 7.5,
                "company_response_rate": 68,
                "is_ghost_job": False,
                "ai_salary_estimate": "₹6LPA - ₹10LPA",
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
    """Browse all real jobs scraped from LinkedIn, Indeed, Glassdoor."""
    jobs = _get_cached_jobs(search_term=search, location=location)
    return {"jobs": jobs[:limit], "total": len(jobs), "source": "jobspy_real"}


@router.get("/matches/{user_id}")
async def get_matched_jobs(
    user_id: str,
    search: str = Query("software engineer"),
    location: str = Query("India"),
    limit: int = Query(20, le=50)
):
    """
    Returns real AI-matched jobs for a user.
    1. Fetch user's resume text from Supabase
    2. Score real scraped jobs against it
    3. Fallback to all jobs if no resume found
    """
    db = get_db()
    resume_text = None

    # Try to fetch resume from Supabase
    if db:
        try:
            res = db.table("resumes").select("parsed_text").eq("user_id", user_id).execute()
            if res.data and res.data[0].get("parsed_text"):
                resume_text = res.data[0]["parsed_text"]
        except Exception as e:
            print(f"DB fetch warning: {e}")

    # Get real scraped jobs
    all_jobs = _get_cached_jobs(search_term=search, location=location)
    
    if resume_text:
        # Simple keyword matching to score jobs
        resume_lower = resume_text.lower()
        for job in all_jobs:
            desc_lower = (job.get("description", "") + " " + job.get("title", "")).lower()
            # Count keyword overlaps
            resume_words = set(resume_lower.split())
            desc_words = set(desc_lower.split())
            overlap = len(resume_words & desc_words)
            score = min(98, 60 + overlap)
            job["match_score"] = score
        
        # Sort by match score
        all_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return {"matches": all_jobs[:limit], "total": len(all_jobs), "source": "jobspy_real"}


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
