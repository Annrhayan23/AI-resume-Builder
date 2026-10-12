import re
import html
import asyncio
from typing import List, Optional
import httpx
from backend.models.schemas import JobPosting, MasterResume
from backend.services.fit_gate import evaluate_candidate_fit

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    # Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', raw_html)
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    # Collapse excess whitespaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

async def fetch_jobicy_jobs(query: str = "", limit: int = 20) -> List[JobPosting]:
    jobs = []
    try:
        url = "https://jobicy.com/api/v2/remote-jobs"
        params = {"count": limit}
        if query:
            params["tag"] = query
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("jobs", [])
                for item in items:
                    job_id = f"jobicy_{item.get('id', '')}"
                    desc = clean_html(item.get("jobDescription", ""))
                    title = clean_html(item.get("jobTitle", "Software Engineer"))
                    company = clean_html(item.get("companyName", "Tech Corp"))
                    location = clean_html(item.get("jobGeo", "Remote"))
                    url_link = item.get("url", "")
                    tags = []
                    if "jobIndustry" in item and item["jobIndustry"]:
                        tags.append(str(item["jobIndustry"]))
                    if "jobType" in item and item["jobType"]:
                        tags.append(str(item["jobType"]))
                    salary = ""
                    if item.get("annualSalaryMin") and item.get("annualSalaryMax"):
                        salary = f"${item.get('annualSalaryMin'):,} - ${item.get('annualSalaryMax'):,} {item.get('salaryCurrency', 'USD')}"
                    
                    jobs.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=company,
                        description=desc,
                        url=url_link,
                        location=location,
                        salary=salary,
                        tags=tags,
                        source="Jobicy",
                        created_at=item.get("pubDate", "")
                    ))
    except Exception as e:
        print(f"Error fetching from Jobicy: {e}")
    return jobs

async def fetch_arbeitnow_jobs(query: str = "", limit: int = 20) -> List[JobPosting]:
    jobs = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", [])
                for item in items:
                    title = clean_html(item.get("title", ""))
                    desc = clean_html(item.get("description", ""))
                    company = clean_html(item.get("company_name", ""))
                    location = clean_html(item.get("location", "Global"))
                    
                    # If query filter provided, check match
                    if query and query.lower() not in title.lower() and query.lower() not in desc.lower():
                        continue
                    
                    job_id = f"arbeitnow_{item.get('slug', item.get('id', ''))}"
                    url_link = item.get("url", "")
                    tags = item.get("tags", [])
                    
                    jobs.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=company,
                        description=desc,
                        url=url_link,
                        location=location,
                        salary="",
                        tags=tags,
                        source="Arbeitnow",
                        created_at=str(item.get("created_at", ""))
                    ))
                    if len(jobs) >= limit:
                        break
    except Exception as e:
        print(f"Error fetching from Arbeitnow: {e}")
    return jobs

async def fetch_remotive_jobs(query: str = "", limit: int = 20) -> List[JobPosting]:
    jobs = []
    try:
        url = "https://remotive.com/api/remote-jobs"
        params = {"limit": limit}
        if query:
            params["search"] = query
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("jobs", [])
                for item in items:
                    job_id = f"remotive_{item.get('id', '')}"
                    title = clean_html(item.get("title", ""))
                    desc = clean_html(item.get("description", ""))
                    company = clean_html(item.get("company_name", ""))
                    location = clean_html(item.get("candidate_required_location", "Remote"))
                    url_link = item.get("url", "")
                    tags = item.get("tags", [])
                    salary = clean_html(item.get("salary", ""))
                    
                    jobs.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=company,
                        description=desc,
                        url=url_link,
                        location=location,
                        salary=salary,
                        tags=tags,
                        source="Remotive",
                        created_at=item.get("publication_date", "")
                    ))
    except Exception as e:
        print(f"Error fetching from Remotive: {e}")
    return jobs

async def search_and_rank_jobs(query: str = "", master_resume: Optional[MasterResume] = None, fit_threshold: int = 50, limit: int = 30) -> List[JobPosting]:
    # Run fetchers in parallel
    results = await asyncio.gather(
        fetch_jobicy_jobs(query=query, limit=15),
        fetch_arbeitnow_jobs(query=query, limit=15),
        fetch_remotive_jobs(query=query, limit=15),
        return_exceptions=True
    )
    
    combined: List[JobPosting] = []
    seen_titles = set()
    
    for res in results:
        if isinstance(res, list):
            for job in res:
                key = f"{job.title.lower().strip()}_{job.company.lower().strip()}"
                if key not in seen_titles:
                    seen_titles.add(key)
                    combined.append(job)
    
    # If master resume provided, score each job's fit!
    if master_resume:
        for job in combined:
            gate_eval = evaluate_candidate_fit(master_resume, job.description, job.title, threshold=fit_threshold)
            job.fit_score = gate_eval.fit_score
            job.fit_passed = gate_eval.passed
            job.knockouts = gate_eval.knockouts
        
        # Sort by fit_score descending (passing jobs first)
        combined.sort(key=lambda j: (1 if j.fit_passed else 0, j.fit_score or 0), reverse=True)
    
    return combined[:limit]
