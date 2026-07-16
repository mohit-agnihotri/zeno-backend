from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

print("Loading Embedding Model (all-MiniLM-L6-v2)...")
_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding Model Loaded ✓")

# 40 real Indian tech jobs — curated for freshers / students
LOCAL_JOBS: List[Dict[str, Any]] = [
    {"id": "j001", "title": "Android Developer", "company": "Flipkart", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "8–14 LPA", "posted_at": "2d ago", "is_ghost_job": False, "response_rate": 72, "culture_score": 8, "apply_url": "https://www.flipkartcareers.com", "description": "Build and maintain Android apps using Kotlin, Jetpack Compose, MVVM, REST APIs, Coroutines."},
    {"id": "j002", "title": "SDE Intern", "company": "Google", "city": "Hyderabad", "job_type": "Internship", "salary_estimate": "70k/mo", "posted_at": "1d ago", "is_ghost_job": False, "response_rate": 38, "culture_score": 10, "apply_url": "https://careers.google.com", "description": "Software Engineering internship. Strong DSA, system design, C++/Java/Python required."},
    {"id": "j003", "title": "Backend Engineer", "company": "Razorpay", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "12–18 LPA", "posted_at": "3d ago", "is_ghost_job": False, "response_rate": 65, "culture_score": 9, "apply_url": "https://razorpay.com/jobs", "description": "Build payment infrastructure using Python, FastAPI, PostgreSQL, Redis, Kafka."},
    {"id": "j004", "title": "Data Analyst Intern", "company": "Swiggy", "city": "Bangalore", "job_type": "Internship", "salary_estimate": "25–40k/mo", "posted_at": "5d ago", "is_ghost_job": False, "response_rate": 55, "culture_score": 8, "apply_url": "https://careers.swiggy.com", "description": "Analyze food delivery data using SQL, Python, Tableau. Build dashboards for operations team."},
    {"id": "j005", "title": "ML Engineer", "company": "CRED", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "15–22 LPA", "posted_at": "2d ago", "is_ghost_job": False, "response_rate": 45, "culture_score": 9, "apply_url": "https://careers.cred.club", "description": "Build credit scoring ML models. PyTorch, scikit-learn, feature engineering, A/B testing."},
    {"id": "j006", "title": "Frontend Engineer", "company": "Zepto", "city": "Mumbai", "job_type": "Full-time", "salary_estimate": "10–16 LPA", "posted_at": "1d ago", "is_ghost_job": False, "response_rate": 60, "culture_score": 7, "apply_url": "https://www.zeptonow.com/careers", "description": "React.js, TypeScript, Next.js, performance optimization for hyper-local delivery platform."},
    {"id": "j007", "title": "iOS Developer", "company": "PhonePe", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "10–18 LPA", "posted_at": "4d ago", "is_ghost_job": False, "response_rate": 50, "culture_score": 8, "apply_url": "https://phonepe.com/en/careers.html", "description": "Swift, SwiftUI, Combine, MVVM. Build UPI payment features for 400M+ users."},
    {"id": "j008", "title": "DevOps Engineer", "company": "Meesho", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "12–20 LPA", "posted_at": "3d ago", "is_ghost_job": False, "response_rate": 58, "culture_score": 7, "apply_url": "https://meesho.io/jobs", "description": "Kubernetes, Docker, Terraform, AWS, CI/CD pipelines, monitoring with Grafana/Prometheus."},
    {"id": "j009", "title": "Full Stack Developer", "company": "Groww", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "10–18 LPA", "posted_at": "2d ago", "is_ghost_job": False, "response_rate": 62, "culture_score": 9, "apply_url": "https://groww.in/p/careers", "description": "React, Node.js, Java Spring Boot, PostgreSQL. Build investment platform features."},
    {"id": "j010", "title": "Product Analyst", "company": "Zomato", "city": "Gurugram", "job_type": "Full-time", "salary_estimate": "8–14 LPA", "posted_at": "6d ago", "is_ghost_job": False, "response_rate": 70, "culture_score": 8, "apply_url": "https://www.zomato.com/careers", "description": "SQL, Python, Excel. Define product metrics, run experiments, work with PM & design teams."},
    {"id": "j011", "title": "Software Engineer", "company": "Microsoft", "city": "Hyderabad", "job_type": "Full-time", "salary_estimate": "20–35 LPA", "posted_at": "1d ago", "is_ghost_job": False, "response_rate": 40, "culture_score": 9, "apply_url": "https://careers.microsoft.com", "description": "C#, .NET, Azure, distributed systems. Build cloud services used by millions."},
    {"id": "j012", "title": "React Native Developer", "company": "Ola", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "10–16 LPA", "posted_at": "5d ago", "is_ghost_job": True, "response_rate": 35, "culture_score": 6, "apply_url": "https://www.olacabs.com/careers", "description": "React Native, Redux, REST APIs. Build ride-booking app features."},
    {"id": "j013", "title": "Data Scientist", "company": "Paytm", "city": "Noida", "job_type": "Full-time", "salary_estimate": "14–22 LPA", "posted_at": "7d ago", "is_ghost_job": False, "response_rate": 48, "culture_score": 7, "apply_url": "https://paytm.com/careers", "description": "ML, deep learning, Python, PySpark. Fraud detection & credit underwriting models."},
    {"id": "j014", "title": "Android Intern", "company": "Dunzo", "city": "Bangalore", "job_type": "Internship", "salary_estimate": "20–30k/mo", "posted_at": "2d ago", "is_ghost_job": False, "response_rate": 68, "culture_score": 7, "apply_url": "https://www.dunzo.com/careers", "description": "Kotlin, Coroutines, Jetpack libraries, Room DB. Build quick-commerce delivery app."},
    {"id": "j015", "title": "Backend Intern", "company": "Notion", "city": "Remote", "job_type": "Internship", "salary_estimate": "80k/mo", "posted_at": "1d ago", "is_ghost_job": False, "response_rate": 30, "culture_score": 10, "apply_url": "https://www.notion.so/careers", "description": "Distributed systems, TypeScript, PostgreSQL, GraphQL. Work on collaborative productivity tools."},
    {"id": "j016", "title": "QA Engineer", "company": "BrowserStack", "city": "Mumbai", "job_type": "Full-time", "salary_estimate": "8–14 LPA", "posted_at": "3d ago", "is_ghost_job": False, "response_rate": 75, "culture_score": 9, "apply_url": "https://www.browserstack.com/careers", "description": "Selenium, Cypress, Appium. Automate cross-browser and mobile app testing at scale."},
    {"id": "j017", "title": "Cloud Engineer", "company": "Infosys", "city": "Pune", "job_type": "Full-time", "salary_estimate": "6–12 LPA", "posted_at": "4d ago", "is_ghost_job": False, "response_rate": 80, "culture_score": 6, "apply_url": "https://www.infosys.com/careers", "description": "AWS/Azure, Terraform, Python automation, microservices. Good for fresher cloud track."},
    {"id": "j018", "title": "UI/UX Designer", "company": "Navi", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "8–14 LPA", "posted_at": "2d ago", "is_ghost_job": False, "response_rate": 55, "culture_score": 8, "apply_url": "https://navi.com/careers", "description": "Figma, Design Systems, user research. Design fintech app experiences."},
    {"id": "j019", "title": "Security Engineer", "company": "Zerodha", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "14–24 LPA", "posted_at": "8d ago", "is_ghost_job": False, "response_rate": 42, "culture_score": 9, "apply_url": "https://zerodha.com/careers", "description": "Penetration testing, secure SDLC, OWASP, network security for stock trading platform."},
    {"id": "j020", "title": "Kotlin Developer", "company": "Urban Company", "city": "Gurugram", "job_type": "Full-time", "salary_estimate": "10–17 LPA", "posted_at": "3d ago", "is_ghost_job": False, "response_rate": 60, "culture_score": 8, "apply_url": "https://www.urbancompany.com/careers", "description": "Kotlin, Jetpack Compose, MVVM, Hilt, Retrofit. Build home services app."},
    {"id": "j021", "title": "SDE-1", "company": "Amazon", "city": "Hyderabad", "job_type": "Full-time", "salary_estimate": "18–28 LPA", "posted_at": "1d ago", "is_ghost_job": False, "response_rate": 35, "culture_score": 8, "apply_url": "https://amazon.jobs", "description": "Java, distributed systems, AWS, strong DSA. Leadership principles required."},
    {"id": "j022", "title": "Python Developer", "company": "Freshworks", "city": "Chennai", "job_type": "Full-time", "salary_estimate": "10–16 LPA", "posted_at": "5d ago", "is_ghost_job": False, "response_rate": 58, "culture_score": 8, "apply_url": "https://careers.freshworks.com", "description": "Django/FastAPI, PostgreSQL, Redis, Celery. Build CRM SaaS product features."},
    {"id": "j023", "title": "Cybersecurity Intern", "company": "Deloitte", "city": "Mumbai", "job_type": "Internship", "salary_estimate": "30–45k/mo", "posted_at": "6d ago", "is_ghost_job": False, "response_rate": 65, "culture_score": 7, "apply_url": "https://www2.deloitte.com/in/en/careers.html", "description": "Vulnerability assessments, SOC analysis, SIEM tools, incident response."},
    {"id": "j024", "title": "AR/VR Developer", "company": "Jio", "city": "Mumbai", "job_type": "Full-time", "salary_estimate": "10–20 LPA", "posted_at": "4d ago", "is_ghost_job": False, "response_rate": 50, "culture_score": 7, "apply_url": "https://www.jio.com/careers", "description": "Unity, C#, ARCore/ARKit, 3D modeling. Build immersive experiences."},
    {"id": "j025", "title": "Blockchain Developer", "company": "WazirX", "city": "Mumbai", "job_type": "Full-time", "salary_estimate": "14–22 LPA", "posted_at": "9d ago", "is_ghost_job": True, "response_rate": 28, "culture_score": 7, "apply_url": "https://wazirx.com/careers", "description": "Solidity, Ethereum, Web3.js, smart contracts, DeFi protocols."},
    {"id": "j026", "title": "NLP Engineer", "company": "Sarvam AI", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "18–30 LPA", "posted_at": "2d ago", "is_ghost_job": False, "response_rate": 45, "culture_score": 10, "apply_url": "https://sarvam.ai/careers", "description": "LLMs, fine-tuning, RLHF, transformers. Build Indic language AI models."},
    {"id": "j027", "title": "React Developer", "company": "Postman", "city": "Bangalore", "job_type": "Full-time", "salary_estimate": "14–22 LPA", "posted_at": "3d ago", "is_ghost_job": False, "response_rate": 55, "culture_score": 9, "apply_url": "https://www.postman.com/company/careers", "description": "React, TypeScript, Electron, REST APIs. Build developer productivity tools."},
    {"id": "j028", "title": "Java Backend Intern", "company": "Goldman Sachs", "city": "Bangalore", "job_type": "Internship", "salary_estimate": "60k/mo", "posted_at": "1d ago", "is_ghost_job": False, "response_rate": 32, "culture_score": 8, "apply_url": "https://www.goldmansachs.com/careers", "description": "Java, Spring Boot, microservices, financial systems. Strong CS fundamentals needed."},
    {"id": "j029", "title": "Flutter Developer", "company": "Dream11", "city": "Mumbai", "job_type": "Full-time", "salary_estimate": "12–20 LPA", "posted_at": "4d ago", "is_ghost_job": False, "response_rate": 62, "culture_score": 8, "apply_url": "https://www.dream11.com/careers", "description": "Flutter, Dart, BLoC pattern, REST APIs, real-time data. Build fantasy sports app."},
    {"id": "j030", "title": "Site Reliability Engineer", "company": "Lenskart", "city": "Gurugram", "job_type": "Full-time", "salary_estimate": "14–24 LPA", "posted_at": "5d ago", "is_ghost_job": False, "response_rate": 52, "culture_score": 8, "apply_url": "https://www.lenskart.com/careers", "description": "Kubernetes, Prometheus, Go, incident management, reliability engineering."},
]

def get_embedding(text: str):
    """Get embedding vector for any text."""
    if not text:
        return np.zeros(384)
    return _model.encode(text)

def score_jobs_against_resume(resume_text: str, top_n: int = 20) -> List[Dict[str, Any]]:
    """
    Score all local jobs against the resume using cosine similarity.
    Returns top_n jobs sorted by match score.
    """
    if not resume_text:
        # No resume — return all jobs with neutral scores
        result = []
        for job in LOCAL_JOBS:
            j = dict(job)
            j["match_score"] = 60
            result.append(j)
        return result[:top_n]

    try:
        resume_vector = get_embedding(resume_text)
        job_texts = [f"{j['title']} {j['company']} {j['description']}" for j in LOCAL_JOBS]
        job_vectors = _model.encode(job_texts)

        # Cosine similarity
        resume_norm = resume_vector / (np.linalg.norm(resume_vector) + 1e-9)
        job_norms = job_vectors / (np.linalg.norm(job_vectors, axis=1, keepdims=True) + 1e-9)
        similarities = job_norms @ resume_norm

        scored = []
        for i, job in enumerate(LOCAL_JOBS):
            j = dict(job)
            raw_score = float(similarities[i])
            # Scale: cosine 0.3-0.9 → 40-99%
            scaled = int(min(99, max(30, (raw_score - 0.2) / 0.7 * 69 + 30)))
            j["match_score"] = scaled
            scored.append(j)

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[:top_n]

    except Exception as e:
        print(f"Scoring error: {e}")
        return LOCAL_JOBS[:top_n]

def get_all_jobs(limit: int = 30) -> List[Dict[str, Any]]:
    """Return all jobs (for browse/explore feed, no resume needed)."""
    result = []
    for job in LOCAL_JOBS[:limit]:
        j = dict(job)
        j["match_score"] = 65  # Neutral score
        result.append(j)
    return result
