from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

class ExperienceItem(BaseModel):
    company: str
    role: str
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    bullets: List[str] = []
    technologies: List[str] = []

class EducationItem(BaseModel):
    institution: str
    degree: str
    field_of_study: str = ""
    graduation_year: str = ""
    gpa: Optional[str] = None
    honors: Optional[str] = None

class ProjectItem(BaseModel):
    name: str
    role: str = ""
    description: str = ""
    bullets: List[str] = []
    technologies: List[str] = []
    link: Optional[str] = None

class MasterResume(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    skills: Dict[str, List[str]] = {}
    experience: List[ExperienceItem] = []
    education: List[EducationItem] = []
    projects: List[ProjectItem] = []
    certifications: List[str] = []

class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    description: str
    url: str = ""
    location: str = ""
    salary: str = ""
    tags: List[str] = []
    source: str = ""
    created_at: str = ""
    fit_score: Optional[int] = None
    fit_passed: Optional[bool] = None
    knockouts: List[str] = []

class FitGateResult(BaseModel):
    passed: bool
    fit_score: int
    threshold: int
    knockouts: List[str] = []
    reason: str
    missing_qualifications: List[str] = []
    domain_match_score: float = 0.0
    experience_match_score: float = 0.0
    actionable_remedies: List[str] = []

class JDAnalysis(BaseModel):
    title: str = ""
    company: str = ""
    domain: str = ""
    seniority_level: str = ""
    required_years_experience: int = 0
    must_have_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    keywords: List[str] = []
    pain_points: List[str] = []
    summary: str = ""

class ATSScoreResult(BaseModel):
    score: int
    keyword_match_rate: float
    evidence_match_pct: float
    missing_keywords: List[str] = []
    matched_keywords: List[str] = []
    section_scores: Dict[str, int] = {}
    formatting_passed: bool = True
    advisory_notes: List[str] = []

class HRScoreResult(BaseModel):
    score: int
    quantified_impact_pct: float
    action_verb_power_pct: float
    seniority_tone_rating: str
    readability_rating: str
    red_flags: List[str] = []
    recruiter_summary: str
    strengths: List[str] = []
    recommendations: List[str] = []

class IterationLog(BaseModel):
    iteration: int
    evidence_match_pct: float
    ats_score: int
    hr_score: int
    improvements_made: List[str] = []

class TailoringRequest(BaseModel):
    job_description: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_url: Optional[str] = None
    fit_bar: int = 50
    evidence_target: int = 75
    max_iterations: int = 3
    master_resume_override: Optional[MasterResume] = None

class TailoringResponse(BaseModel):
    success: bool
    fit_gate: FitGateResult
    jd_analysis: Optional[JDAnalysis] = None
    tailored_resume: Optional[MasterResume] = None
    cover_letter: Optional[str] = None
    iterations: List[IterationLog] = []
    final_ats: Optional[ATSScoreResult] = None
    final_hr: Optional[HRScoreResult] = None
    resume_docx_filename: Optional[str] = None
    cover_letter_docx_filename: Optional[str] = None
    application_id: Optional[str] = None
    error_message: Optional[str] = None

class ApplicationRecord(BaseModel):
    id: str
    date: str
    company: str
    role: str
    url: str = ""
    fit_score: int = 0
    gate_status: str = "Passed"
    ats_score: int = 0
    hr_score: int = 0
    evidence_match: float = 0.0
    resume_file: str = ""
    cover_letter_file: str = ""
    status: str = "Ready"  # Ready, Applied, Screening, Interview, Offer, Rejected
    notes: str = ""

class UpdateStatusRequest(BaseModel):
    application_id: str
    status: str
    notes: Optional[str] = None

class SettingsPayload(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = "gemini-2.5-flash"
    fit_bar_threshold: Optional[int] = 50
    evidence_match_target: Optional[int] = 75
    max_iterations: Optional[int] = 3
