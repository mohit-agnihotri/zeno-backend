from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
import uuid
from datetime import datetime

router = APIRouter(prefix="/tracker", tags=["Application Tracker"])

class ApplicationCreate(BaseModel):
    user_id: str
    job_title: str
    company: str
    city: Optional[str] = "Remote"
    job_type: Optional[str] = "Full-time"
    apply_url: Optional[str] = ""
    notes: Optional[str] = ""

class ApplicationStatusUpdate(BaseModel):
    status: str  # "applied", "viewed", "replied", "offer", "rejected"


@router.get("/{user_id}")
async def get_applications(user_id: str):
    """Get all tracked applications for a user from Supabase."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected. Please configure SUPABASE_URL and SUPABASE_KEY.")
    
    try:
        res = db.table("applications").select("*").eq("user_id", user_id).order("applied_at", desc=True).execute()
        return {"applications": res.data or [], "source": "supabase"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch applications: {str(e)}")


@router.post("/add")
async def add_application(app: ApplicationCreate):
    """Log a new job application to Supabase."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected.")
    
    try:
        res = db.table("applications").insert({
            "user_id": app.user_id,
            "job_title": app.job_title,
            "company": app.company,
            "city": app.city,
            "job_type": app.job_type,
            "apply_url": app.apply_url,
            "notes": app.notes,
            "status": "applied",
        }).execute()
        return {"message": "Application logged!", "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add application: {str(e)}")


@router.patch("/{application_id}/status")
async def update_status(application_id: str, update: ApplicationStatusUpdate):
    """Update the status of an application in Supabase."""
    valid_statuses = ["applied", "viewed", "replied", "offer", "rejected"]
    if update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected.")
    
    try:
        update_data = {"status": update.status}
        # Record timestamp for seen/replied
        if update.status == "viewed":
            update_data["seen_at"] = datetime.utcnow().isoformat()
        elif update.status == "replied":
            update_data["replied_at"] = datetime.utcnow().isoformat()
        
        db.table("applications").update(update_data).eq("id", application_id).execute()
        return {"message": "Status updated!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{application_id}")
async def delete_application(application_id: str):
    """Delete a tracked application from Supabase."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected.")
        
    try:
        db.table("applications").delete().eq("id", application_id).execute()
        return {"message": "Application removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
