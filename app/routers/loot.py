import feedparser
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import httpx
import google.generativeai as genai
import json
import os
import time
import asyncio

router = APIRouter(prefix="/loot", tags=["Loot & Hackathons"])

class LootItem(BaseModel):
    id: str
    title: str
    company: str
    description: str
    applyUrl: str
    imageUrl: str
    type: str # "hackathon", "certification", "offcampus"
    deadline: Optional[str] = "Check website"
    isPremium: bool = False

# Hardcoded but REAL certifications that are currently free
FREE_CERTS = [
    LootItem(
        id="cert-google-1",
        title="Google Cloud Digital Leader",
        company="Google",
        description="Learn core cloud concepts and how Google Cloud products are used to achieve digital transformation.",
        applyUrl="https://cloud.google.com/training/cloud-digital-leader",
        imageUrl="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg",
        type="certification"
    ),
    LootItem(
        id="cert-ms-1",
        title="Microsoft Azure AI Fundamentals",
        company="Microsoft",
        description="Demonstrate fundamental AI concepts related to the development of software and services of Microsoft Azure.",
        applyUrl="https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-fundamentals/?practice-assessment-type=certification",
        imageUrl="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg",
        type="certification"
    ),
    LootItem(
        id="cert-aws-1",
        title="AWS Cloud Practitioner",
        company="AWS",
        description="Overall understanding of the AWS Cloud platform, covering basic cloud concepts and security.",
        applyUrl="https://aws.amazon.com/certification/certified-cloud-practitioner/",
        imageUrl="https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg",
        type="certification"
    )
]

# --- AI VALIDATED REDDIT CACHE ---
reddit_certs_cache = {
    "timestamp": 0,
    "certs": []
}
CACHE_TTL = 3600 * 2  # 2 hours

async def fetch_reddit_certs_with_ai() -> List[LootItem]:
    """Fetch live certification discussions from Reddit and validate with Gemini."""
    current_time = time.time()
    if current_time - reddit_certs_cache["timestamp"] < CACHE_TTL and reddit_certs_cache["certs"]:
        return reddit_certs_cache["certs"]

    # Limit to 10 latest posts across relevant subreddits
    url = "https://www.reddit.com/r/AWSCertifications+AzureCertification+ITCertifications+freecertifications/search.json?q=free+OR+voucher+OR+discount+OR+100%25&restrict_sr=on&sort=new&limit=10"
    headers = {"User-Agent": "ZenoCareerApp/1.0 (Contact: admin@zenoapp.com)"}
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            
        if resp.status_code != 200:
            return []
            
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        
        valid_certs = []
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        for post in posts:
            post_data = post["data"]
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            post_url = "https://reddit.com" + post_data.get("permalink", "")
            url_link = post_data.get("url", post_url)
            
            prompt = f"""
            You are an AI validating free certification vouchers for students.
            Analyze the following Reddit post. Does it contain a legitimate, actual 100% free or heavily discounted IT/Software certification voucher or event?
            Ignore general advice posts. Look for actual offers, links, or challenge announcements.
            
            Title: {title}
            Content: {selftext}
            
            Respond strictly in JSON format (do not use markdown blocks):
            {{
                "is_legit": true/false,
                "cert_name": "Name of the certification or event (keep it concise)",
                "reason": "short 1 sentence reason"
            }}
            """
            
            try:
                ai_resp = model.generate_content(prompt)
                raw_text = ai_resp.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()
                    
                result = json.loads(raw_text)
                
                if result.get("is_legit") == True:
                    valid_certs.append(LootItem(
                        id=f"reddit-{post_data.get('id')}",
                        title=result.get("cert_name", title[:30]),
                        company="Reddit Community",
                        description=f"{result.get('reason', 'Valid free certification voucher.')} (Verified by Zeno AI)",
                        applyUrl=url_link,
                        imageUrl="https://upload.wikimedia.org/wikipedia/commons/b/b4/Reddit_logo.svg",
                        type="certification",
                        isPremium=True
                    ))
            except Exception as e:
                print(f"Gemini parsing error for Reddit post: {e}")
                continue
                
        if valid_certs:
            reddit_certs_cache["certs"] = valid_certs
            reddit_certs_cache["timestamp"] = current_time
            
        return valid_certs
        
    except Exception as e:
        print(f"Error fetching/validating Reddit certs: {e}")
        return []

def fetch_hackathons() -> List[LootItem]:
    """Fetch real hackathons from Devpost RSS feed."""
    try:
        feed = feedparser.parse('https://devpost.com/hackathons.atom')
        hackathons = []
        for entry in feed.entries[:5]:  # Get latest 5
            hackathons.append(LootItem(
                id=entry.id if hasattr(entry, 'id') else entry.link,
                title=entry.title,
                company="Devpost",
                description=entry.summary[:150] + "..." if hasattr(entry, 'summary') else "",
                applyUrl=entry.link,
                imageUrl="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/GitHub_Invertocat_Logo.svg/1200px-GitHub_Invertocat_Logo.svg.png", # Placeholder
                type="hackathon"
            ))
        return hackathons
    except Exception as e:
        print(f"Error fetching Devpost RSS: {e}")
        return []

def fetch_offcampus() -> List[LootItem]:
    """Fetch off-campus drives. (Mocking Unstop RSS for now as it frequently blocks raw requests)"""
    # In production, we'd use feedparser.parse('https://unstop.com/opportunity/rss')
    # but for stability in this beta, we provide realistic curated ongoing drives.
    return [
        LootItem(
            id="drive-1",
            title="TCS Smart Hiring 2026",
            company="TCS",
            description="TCS Smart Hiring is exclusively for BCA, B.Sc (Maths, Statistics, Physics, Chemistry, Electronics, Biochemistry, Computer Science, IT) graduates.",
            applyUrl="https://www.tcs.com/careers/india/tcs-smart-hiring",
            imageUrl="https://upload.wikimedia.org/wikipedia/commons/b/b1/Tata_Consultancy_Services_Logo.svg",
            type="offcampus",
            isPremium=True
        ),
        LootItem(
            id="drive-2",
            title="Wipro Elite NTH",
            company="Wipro",
            description="National Talent Hunt (NTH) is our fresher hiring program to attract the best of 2025/2026 engineering talent.",
            applyUrl="https://careers.wipro.com/elite",
            imageUrl="https://upload.wikimedia.org/wikipedia/commons/a/a0/Wipro_Primary_Logo_Color_RGB.svg",
            type="offcampus"
        )
    ]

@router.get("/feed")
async def get_loot_feed(type: str = "all"):
    """
    Returns real hackathons, certifications, and off-campus drives.
    Query param `type` can be 'all', 'hackathon', 'certification', or 'offcampus'.
    """
    feed = []
    
    if type in ["all", "certification"]:
        feed.extend(FREE_CERTS)
        reddit_certs = await fetch_reddit_certs_with_ai()
        feed.extend(reddit_certs)
        
    if type in ["all", "hackathon"]:
        feed.extend(fetch_hackathons())
        
    if type in ["all", "offcampus"]:
        feed.extend(fetch_offcampus())
        
    # Shuffle or sort by some metric if needed. For now, just return.
    return {"loot": feed, "source": "devpost_rss_and_curated"}
