import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import (
    BASE_DIR, DATA_DIR, OUTPUT_DIR, MASTER_RESUME_FILE,
    APPLICATIONS_FILE, load_settings, save_settings
)
from backend.models.schemas import (
    MasterResume, JobPosting, FitGateResult, JDAnalysis,
    TailoringRequest, TailoringResponse, ApplicationRecord,
    UpdateStatusRequest, SettingsPayload
)
from backend.services.job_service import search_and_rank_jobs
from backend.services.fit_gate import evaluate_candidate_fit
from backend.services.jd_analyzer import analyze_job_description
from backend.services.tailoring_engine import run_tailoring_pipeline
from backend.services.docx_generator import generate_resume_docx, generate_cover_letter_docx
from backend.services.excel_tracker import (
    init_excel_tracker, add_application, get_all_applications, update_application_status
)

app = FastAPI(
    title="AI Resume & Cover Letter Generator with Dual ATS + HR Scoring",
    description="Live job discovery, strict candidate fit gating, truthful tailoring, dual heuristic scoring, and Excel tracking.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage on startup
init_excel_tracker()

def get_current_master_resume() -> MasterResume:
    if MASTER_RESUME_FILE.exists():
        try:
            with open(MASTER_RESUME_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return MasterResume(**data)
        except Exception as e:
            print(f"Error reading master resume: {e}")
    return MasterResume()

# --- Endpoints ---

@app.get("/api/master-resume", response_model=MasterResume)
def get_master_resume():
    return get_current_master_resume()

@app.post("/api/master-resume")
def save_master_resume(resume: MasterResume):
    with open(MASTER_RESUME_FILE, "w", encoding="utf-8") as f:
        f.write(resume.model_dump_json(indent=2))
    return {"message": "Master resume updated successfully."}

@app.get("/api/jobs/search", response_model=List[JobPosting])
async def search_jobs(
    query: str = Query(default="", description="Search keywords"),
    limit: int = Query(default=25, description="Number of results")
):
    master = get_current_master_resume()
    settings = load_settings()
    threshold = settings.get("fit_bar_threshold", 50)
    jobs = await search_and_rank_jobs(
        query=query,
        master_resume=master,
        fit_threshold=threshold,
        limit=limit
    )
    return jobs

@app.post("/api/fit-gate", response_model=FitGateResult)
def test_fit_gate(
    job_description: str = Body(..., embed=True),
    job_title: str = Body(default="", embed=True),
    threshold: Optional[int] = Body(default=None, embed=True)
):
    master = get_current_master_resume()
    settings = load_settings()
    bar = threshold if threshold is not None else settings.get("fit_bar_threshold", 50)
    return evaluate_candidate_fit(master, job_description, job_title, threshold=bar)

@app.post("/api/analyze-jd", response_model=JDAnalysis)
def analyze_jd(
    job_description: str = Body(..., embed=True),
    job_title: str = Body(default="", embed=True),
    company_name: str = Body(default="", embed=True)
):
    return analyze_job_description(job_description, job_title, company_name)

@app.post("/api/tailor", response_model=TailoringResponse)
def tailor_resume(payload: TailoringRequest):
    # 1. Load Master Resume
    master = payload.master_resume_override if payload.master_resume_override else get_current_master_resume()
    
    # 2. Strict Fit Gating Step
    fit_gate = evaluate_candidate_fit(
        master,
        payload.job_description,
        payload.job_title or "",
        threshold=payload.fit_bar
    )
    
    # If fit gate fails, HALT immediately and refuse to fabricate experience!
    if not fit_gate.passed:
        return TailoringResponse(
            success=False,
            fit_gate=fit_gate,
            error_message=fit_gate.reason
        )
        
    # 3. Analyze JD
    jd_analysis = analyze_job_description(
        payload.job_description,
        payload.job_title or "Software Engineer",
        payload.company_name or "Target Company"
    )
    
    # 4. Tailoring & Iteration Pipeline
    tailored_resume, cover_letter, iterations, final_ats, final_hr = run_tailoring_pipeline(
        master_resume=master,
        jd=jd_analysis,
        fit_gate=fit_gate,
        evidence_target=payload.evidence_target,
        max_iterations=payload.max_iterations
    )
    
    # 5. Generate Production-Ready DOCX Files
    safe_company = "".join(c for c in (payload.company_name or "Company") if c.isalnum() or c in ('_', '-'))
    safe_role = "".join(c for c in (payload.job_title or "Role") if c.isalnum() or c in ('_', '-'))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    resume_filename_prefix = f"Resume_{safe_company}_{safe_role}_{timestamp}"
    cover_letter_filename_prefix = f"CoverLetter_{safe_company}_{safe_role}_{timestamp}"
    
    resume_docx = generate_resume_docx(tailored_resume, filename_prefix=resume_filename_prefix)
    cover_letter_docx = generate_cover_letter_docx(tailored_resume, cover_letter, filename_prefix=cover_letter_filename_prefix)
    
    # 6. Track Application in Excel Spreadsheet
    app_id = str(uuid.uuid4())[:8]
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    record = ApplicationRecord(
        id=app_id,
        date=date_str,
        company=payload.company_name or "Target Company",
        role=payload.job_title or "Software Engineer",
        url=payload.job_url or "",
        fit_score=fit_gate.fit_score,
        gate_status="Cleared",
        ats_score=final_ats.score,
        hr_score=final_hr.score,
        evidence_match=final_ats.evidence_match_pct,
        resume_file=resume_docx,
        cover_letter_file=cover_letter_docx,
        status="Ready",
        notes=f"Auto-tailored in {len(iterations)} iteration(s). Evidence match: {final_ats.evidence_match_pct}%"
    )
    add_application(record)
    
    return TailoringResponse(
        success=True,
        fit_gate=fit_gate,
        jd_analysis=jd_analysis,
        tailored_resume=tailored_resume,
        cover_letter=cover_letter,
        iterations=iterations,
        final_ats=final_ats,
        final_hr=final_hr,
        resume_docx_filename=resume_docx,
        cover_letter_docx_filename=cover_letter_docx,
        application_id=app_id
    )

@app.get("/api/tracker/applications", response_model=List[ApplicationRecord])
def list_applications():
    return get_all_applications()

@app.post("/api/tracker/update-status")
def update_status(payload: UpdateStatusRequest):
    success = update_application_status(payload.application_id, payload.status, payload.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Application record not found")
    return {"message": "Status updated successfully."}

@app.get("/api/download/{filename}")
def download_file(filename: str):
    if filename == "applications.xlsx":
        if not APPLICATIONS_FILE.exists():
            init_excel_tracker()
        return FileResponse(
            path=str(APPLICATIONS_FILE),
            filename="Job_Applications_Tracker.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get("/api/settings")
def get_settings():
    s = load_settings()
    # Mask API key for security
    raw_key = s.get("gemini_api_key", "")
    masked_key = f"{raw_key[:4]}...{raw_key[-4:]}" if len(raw_key) > 8 else ("***" if raw_key else "")
    return {
        "gemini_api_key_masked": masked_key,
        "has_api_key": bool(raw_key),
        "gemini_model": s.get("gemini_model", "gemini-2.5-flash"),
        "fit_bar_threshold": s.get("fit_bar_threshold", 50),
        "evidence_match_target": s.get("evidence_match_target", 75),
        "max_iterations": s.get("max_iterations", 3),
    }

@app.post("/api/settings")
def update_settings(payload: SettingsPayload):
    current = load_settings()
    if payload.gemini_api_key is not None and payload.gemini_api_key.strip():
        current["gemini_api_key"] = payload.gemini_api_key.strip()
    if payload.gemini_model:
        current["gemini_model"] = payload.gemini_model
    if payload.fit_bar_threshold is not None:
        current["fit_bar_threshold"] = payload.fit_bar_threshold
    if payload.evidence_match_target is not None:
        current["evidence_match_target"] = payload.evidence_match_target
    if payload.max_iterations is not None:
        current["max_iterations"] = payload.max_iterations
    save_settings(current)
    return {"message": "Settings updated successfully."}

# Mount static frontend build if it exists
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
