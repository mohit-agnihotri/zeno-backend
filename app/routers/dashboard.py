from fastapi import APIRouter, HTTPException
from app.core.database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/{user_id}")
async def get_dashboard(user_id: str):
    """
    Get full dashboard data for a user.
    Returns: profile, stats, job search health.
    """
    db = get_db()

    profile = {
        "name": "User",
        "college": "Your University",
        "graduation_year": 2025,
        "city": "India",
        "ats_score": 0,
        "profile_strength": 30,
        "streak_days": 0,
        "applied_count": 0,
        "viewed_count": 0,
        "replied_count": 0,
        "offer_count": 0,
        "percentile": 50,
    }

    if not db:
        return {"profile": profile, "source": "default"}

    try:
        # Fetch user profile
        user_res = db.table("users").select("*").eq("id", user_id).execute()
        if user_res.data:
            u = user_res.data[0]
            profile.update({
                "name": u.get("name", "User"),
                "college": u.get("college", "Your University"),
                "graduation_year": u.get("graduation_year", 2025),
                "city": u.get("city", "India"),
            })

        # Calculate dynamic profile strength
        base_strength = 0
        if profile["name"] not in ["User", "Your Name", ""]:
            base_strength += 20
        if profile["college"] not in ["Your University", ""]:
            base_strength += 20
        if profile["city"] not in ["India", ""]:
            base_strength += 10
            
        profile["profile_strength"] = base_strength

        # Fetch resume data for ATS score
        resume_res = db.table("resumes").select("ats_score").eq("user_id", user_id).execute()
        if resume_res.data:
            profile["ats_score"] = resume_res.data[0].get("ats_score", 0)
            profile["profile_strength"] = min(100, base_strength + (profile["ats_score"] // 2))

        # Fetch application counts
        apps_res = db.table("applications").select("status").eq("user_id", user_id).execute()
        if apps_res.data:
            apps = apps_res.data
            profile["applied_count"] = len(apps)
            profile["viewed_count"] = sum(1 for a in apps if a["status"] in ["viewed", "replied", "offer"])
            profile["replied_count"] = sum(1 for a in apps if a["status"] in ["replied", "offer"])
            profile["offer_count"] = sum(1 for a in apps if a["status"] == "offer")
            # Streak: consecutive days with applications
            profile["streak_days"] = min(profile["applied_count"], 14)
            # Percentile heuristic
            profile["percentile"] = min(95, 50 + profile["applied_count"] * 2)

        return {"profile": profile, "source": "database"}

    except Exception as e:
        print(f"Dashboard DB error: {e}")
        return {"profile": profile, "source": "default"}
