from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

class ProfileUpdateRequest(BaseModel):
    user_id: str
    name: str
    college: str
    city: str
    graduation_year: int
    linkedin: str = ""

@router.post("/profile")
async def update_profile(req: ProfileUpdateRequest):
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    try:
        # Check if user exists
        user_res = db.table("users").select("*").eq("id", req.user_id).execute()
        
        data = {
            "name": req.name,
            "college": req.college,
            "city": req.city,
            "graduation_year": req.graduation_year,
            "linkedin": req.linkedin
        }
        
        if len(user_res.data) > 0:
            # Update existing
            db.table("users").update(data).eq("id", req.user_id).execute()
        else:
            # Insert new
            data["id"] = req.user_id
            db.table("users").insert(data).execute()
            
        return {"message": "Profile updated successfully"}
    except Exception as e:
        print(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
