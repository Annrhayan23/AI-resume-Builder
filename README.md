<img width="1918" height="947" alt="Screenshot 2026-10-12 220025" src="https://github.com/user-attachments/assets/1a6b880a-d84e-42db-af5a-a04bd505c70a" /># AI-Powered Resume & Cover Letter Generator

An AI-assisted, full-stack application that discovers relevant job opportunities, evaluates candidate-job compatibility, tailors resumes and cover letters, scores application quality, and tracks applications automatically.

## Overview

Applying for jobs often requires manually searching job boards, analyzing job descriptions, customizing resumes, writing cover letters, and tracking application statuses.

This project streamlines that workflow using Python, FastAPI, React, and Google Gemini. It prioritizes truthful resume customization by using the candidate's existing skills and experience rather than inventing qualifications to match a job description.

## Key Features

- **Live Job Discovery:** Aggregates public job listings from Arbeitnow, Jobicy, and Remotive.
- **Candidate Fit Gate:** Evaluates candidate-job compatibility and checks for critical disqualifiers before allowing resume tailoring.
- **Job Description Analysis:** Extracts seniority, required experience, must-have skills, preferred skills, keywords, and employer pain points.
- **AI-Powered Resume Tailoring:** Reframes authentic experience using Google's XYZ formula: *Accomplished X, as measured by Y, by doing Z.*
- **Automated Evidence Matching:** Iteratively improves the alignment between existing candidate evidence and essential job requirements, targeting at least 75% coverage.
- **Dual Advisory Scoring:**
  - ATS scoring for keyword coverage, semantic relevance, and evidence alignment.
  - HR scoring for quantified achievements, action verbs, readability, and cliché detection.
- **Cover Letter Generation:** Creates role-specific cover letters based on the job description and candidate profile.
- **Professional DOCX Export:** Generates ATS-friendly, single-column resumes and matching cover letters.
- **Excel Application Tracker:** Records applications, scores, and statuses in an Excel workbook.
- **Interactive Dashboard:** Provides job search, resume editing, scoring insights, document downloads, and application management.
- **Configurable Settings:** Supports fit thresholds, evidence coverage targets, AI model selection, and Gemini API configuration.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Lucide Icons |
| Backend | Python, FastAPI |
| AI Integration | Google Gemini API |
| Job Sources | Arbeitnow, Jobicy, Remotive |
| Document Generation | python-docx |
| Excel Management | openpyxl |
| Testing | Python backend tests, FastAPI integration tests |

## Architecture

```text
                   ┌─────────────────────────┐
                   │     React Frontend      │
                   │ Dashboard, Job Search,  │
                   │ Resume & Scoring Studio │
                   └────────────┬────────────┘
                                │ REST API
                   ┌────────────▼────────────┐
                   │     FastAPI Backend     │
                   └────────────┬────────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
     ┌───────▼────────┐ ┌───────▼────────┐ ┌───────▼────────┐
     │ Job Discovery  │ │ Candidate Fit  │ │ JD Analyzer    │
     │ Service        │ │ Gate           │ │                │
     └────────────────┘ └────────────────┘ └────────────────┘
                                │
                   ┌────────────▼────────────┐
                   │   Tailoring Engine      │
                   │ Truthful Rewriting &    │
                   │ Evidence Iteration      │
                   └────────────┬────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
             ┌──────▼──────┐         ┌──────▼──────┐
             │ ATS Scorer  │         │ HR Scorer   │
             └──────┬──────┘         └──────┬──────┘
                    │                       │
                    └───────────┬───────────┘
                                │
                   ┌────────────▼────────────┐
                   │ DOCX Documents & Excel  │
                   │ Application Tracker     │
                   └─────────────────────────┘
```

## Project Structure

```text
AI-Resume-Cover-Letter-Generator/
├── backend/
│   ├── app.py
│   ├── services/
│   │   ├── job_service.py
│   │   ├── fit_gate.py
│   │   ├── jd_analyzer.py
│   │   ├── tailoring_engine.py
│   │   ├── ats_scorer.py
│   │   ├── hr_scorer.py
│   │   ├── docx_generator.py
│   │   └── excel_tracker.py
│   └── data/
│       └── applications.xlsx
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── test_backend.py
├── verify_app.py
├── run.py
├── requirements.txt
└── README.md
```

*Note: The structure above reflects the described components. Adjust filenames and folders to match the actual repository.*

## Prerequisites

- Python 3.10 or a compatible version supported by the dependencies
- Node.js and npm
- Git
- A Google Gemini API key for AI-powered functionality

## Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AI-Resume-Cover-Letter-Generator
```

### 2. Create a Python virtual environment

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure the Gemini API key

Configure your Gemini API key through the application's settings interface or the environment variable expected by the backend.

Keep API keys private. Do not commit credentials, `.env` files, or other secrets to GitHub.

### 6. Start the application

From the project root, run:

**Windows PowerShell:**

```powershell
.\venv\Scripts\python run.py
```

The application is configured to launch at:

`http://localhost:8000`

Ensure the frontend dependencies and build process are configured as required by `run.py`.

## How It Works

1. Load the candidate's master resume.
2. Discover available job listings from supported public feeds.
3. Evaluate compatibility and check mandatory disqualifiers.
4. Stop tailoring when the candidate fails the configured fit gate.
5. Extract relevant requirements from the selected job description.
6. Tailor the resume using authentic candidate evidence.
7. Iterate toward the configured must-have evidence coverage target.
8. Calculate ATS and HR advisory scores.
9. Generate the resume and cover letter as DOCX files.
10. Record the application and its status in the Excel tracker.

## Testing

Run the backend service tests:

```bash
python test_backend.py
```

Run the end-to-end integration verification:

```bash
python verify_app.py
```

The reported test results include candidate fit-gate scenarios, job description analysis, resume tailoring, evidence matching, document generation, Excel tracking, and API endpoint verification.

**Reported validation results:**
- Passing and knockout candidate-fit scenarios verified.
- Must-have evidence coverage reached 100% in tested scenarios.
- ATS scores reached 99/100 and HR scores reached 97/100 in reported tests.
- DOCX downloads, tracker updates, and tested API endpoints worked successfully.

These are project-reported results and should not be interpreted as independently audited production benchmarks.

## Application Workflow

**Discover → Evaluate Fit → Analyze JD → Tailor → Score → Generate Documents → Track Application**

The fit gate prevents the tailoring workflow from proceeding when predefined suitability criteria are not met. The system is designed to improve presentation and relevance without fabricating experience, certifications, or achievements.

## Responsible AI and Limitations

- Generated content depends on the accuracy and completeness of the master resume.
- AI-generated content should be reviewed before submission.
- ATS and HR scores are heuristic estimates, not official employer evaluations.
- Job feed availability and listing freshness depend on external sources.
- The evidence coverage target is a configured optimization goal, not a guarantee that the candidate possesses every required qualification.
- Production deployment requires appropriate authentication, secret management, input validation, logging, and security review.

## Future Enhancements

- Add more job-board integrations.
- Introduce application reminders and follow-up notifications.
- Add resume version history and document comparison.
- Improve semantic matching with embedding-based similarity.
- Add analytics for application-to-interview conversion rates.
- Support cloud deployment and secure multi-user access.



[Uploading Screenshot 2026-10-12 220025.png…]()
<img width="1919" height="874" alt="Screenshot 2026-10-12 220035" src="https://github.com/user-attachments/assets/a6d089f0-81c5-4f7c-9532-3814404684ae" />
<img width="1919" height="947" alt="Screenshot 2026-10-12 220043" src="https://github.com/user-attachments/assets/1d00a9e8-2b3a-49b6-8f87-2510c5c62cd0" />
<img width="1919" height="971" alt="Screenshot 2026-10-12 220053" src="https://github.com/user-attachments/assets/00945b4d-dd91-4a96-9bd5-c018ca81df7d" />
<img width="1919" height="957" alt="Screenshot 2026-10-12 220102" src="https://github.com/user-attachments/assets/d8fbda6a-8ee8-4613-a6ce-96549b21d2bb" />




---



*Designed to make job applications more targeted, efficient, and truthful.*<img width="1919" height="957" alt="Screenshot 2026-10-12 220102" src="https://github.com/user-attachments/assets/19a31107-e605-4335-b525-3c5f503cdb79" />
