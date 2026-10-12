AI-Powered Resume & Cover Letter Generator
We have designed, built, and verified a production-grade full-stack system that discovers live jobs, strictly gates candidate fit with zero hard knockouts, analyzes passing job descriptions, tailors master resumes and cover letters using truthful Google XYZ bullet reframing, evaluates applications with dual independent advisory heuristics (ATS semantic match + HR executive recruiter review), auto-iterates to achieve 75%+ must-have evidence coverage, generates production-ready .docx files, and tracks every application in an Excel spreadsheet (applications.xlsx).

🌟 What Was Built
Mermaid diagram
1. Backend Engine (backend/)
Live Job Board Discovery (
backend/services/job_service.py
):
Parallel aggregation across Arbeitnow, Jobicy, and Remotive public feeds.
Pre-screens every discovered job against the candidate's master resume, ranking jobs by fit score.
Strict Candidate Fit Gate (
backend/services/fit_gate.py
):
Evaluates fit bar (default 50/100) and scans for hard knockouts:
Mandatory active security clearance or professional licenses.
Extreme seniority tier deficit (e.g., Junior/Mid applying for Executive/Director/VP).
Years of experience shortfall (>5 years below required).
Zero transferable foundation.
Honest Refusal Policy: If the fit bar is not cleared or a knockout is triggered, tailoring halts immediately with an explicit diagnostic explanation: "No tool that invents experience to close the gap is working for you."
JD Intelligence Extractor (
backend/services/jd_analyzer.py
):
Decomposes job descriptions into primary domain, seniority level, estimated required years, must-have skills, preferred skills, core keywords, and pain points.
Truthful Tailoring & Auto-Iteration Engine (
backend/services/tailoring_engine.py
):
Rewrites bullet points using Google's XYZ formula ([Accomplished X as measured by Y by doing Z]).
Reorders skills and sections to prioritize high-value competencies for the role.
Auto-Iteration Loop: Continues refining and emphasizing authentic dormant experience until the must-have evidence match reaches 75%+ (or max configured iterations).
Generates a tailored, persuasive cover letter addressing the specific hiring team and role challenges.
Dual Advisory Heuristics:
Heuristic 1: ATS & Keyword Semantic Match (
backend/services/ats_scorer.py
): Exact keyword coverage, section density, and evidence match percentage.
Heuristic 2: HR & Executive Recruiter Review (
backend/services/hr_scorer.py
): Quantified impact density (% of bullets with numeric metrics), action verb power rating, readability skim-test score, and cliché red flag detection.
Production DOCX Generator (
backend/services/docx_generator.py
):
Generates 100% ATS-parseable single-column DOCX resumes with executive styling (Calibri, navy accents, divider lines).
Generates formatted DOCX cover letters with matching letterhead.
Excel Application Tracker (
backend/services/excel_tracker.py
):
Automatically records every tailored application in backend/data/applications.xlsx using openpyxl.
Includes styled navy headers, zebra striping, auto-width columns, and status workflows (Ready, Applied, Screening, Interview, Offer, Rejected).
FastAPI REST API (
backend/app.py
):
Exposes REST endpoints for search, fit gating, tailoring, downloads, settings, and serves the static frontend.
2. Modern Web Frontend (frontend/)
Built with React 18 + Vite + Tailwind CSS + Lucide Icons.
Dashboard: High-level KPIs (Total Tracked, Avg ATS Score, Avg HR Score, Pass Rate), workflow overview, and recent applications table.
Live Job Board: Interactive job search with real-time fit score badges (Fit Cleared: XX/100 vs Fit Gated: Knockout Triggered) and 1-click tailoring action.
Tailor & Dual Scoring Studio:
Paste any JD (or use quick 1-click sample presets: "Load Matching JD" or "Load Knockout JD").
Fit Bar slider (default 50) and Evidence Target slider (default 75%).
Prominent Fit Gate System Halt Banner when fit threshold is not met.
Multi-round auto-iteration progression stepper.
Side-by-side Dual Scoring advisory cards (ATS Score + HR Recruiter Review).
Production document download buttons (.docx) with in-browser previews.
Master Resume Manager: Form and raw JSON editor for viewing and updating the master profile.
Excel Tracker Table: Real-time table synchronized with applications.xlsx, status updater, and one-click Excel download.
Settings Modal: Gemini API key management, model selection (gemini-2.5-flash), and threshold configuration.
🧪 Validation & Test Results
1. Backend Service & Heuristics Tests (test_backend.py)
Ran test_backend.py to verify all services:

Master Resume Loading: Loaded 3 experiences, 5 skill categories for candidate Alex Mercer.
Candidate Fit Gate (Passing JD): Fit score 95/100, Passed True, 0 knockouts detected.
Candidate Fit Gate (Knockout JD): Detected mandatory TS/SCI clearance knockout, fit score 35/100, Passed False. Gated and stopped tailoring.
JD Analysis: Extracted domain (Cloud & Infrastructure), seniority (Senior), must-haves (Python, React, Fastapi, Aws).
Tailoring Pipeline & Auto-Iteration: Cleared 100.0% must-have evidence match (surpassing 75% target), final ATS score 99/100, final HR score 97/100 (94.1% quantified metrics).
DOCX Generation: Generated valid Test_Resume_Acme.docx and Test_CoverLetter_Acme.docx.
Excel Tracker: Verified row insertion and auto-formatting in applications.xlsx.
2. End-to-End System Integration Tests (verify_app.py)
Ran verify_app.py to verify full FastAPI server and frontend bundle delivery:

GET /: Status 200 (HTML bundle served correctly).
GET /api/master-resume: Status 200 (Alex Mercer).
POST /api/fit-gate: Verified passing (90/100) and knockout detection (29/100 with 2 knockouts).
POST /api/tailor: Successfully generated tailored resume, cover letter, ATS score 95, HR score 97, and 100% evidence match.
GET /api/tracker/applications: Status 200 with applications synced.
GET /api/download/{filename}: Verified 38 KB DOCX payload delivery.
GET /api/settings: Verified settings retrieval.
All test suites passed 100%.

🚀 How to Run the Application
To launch the web interface:

powershell

.\venv\Scripts\python run.py
This automatically starts the server at http://localhost:8000 and opens the web application in your default browser.
