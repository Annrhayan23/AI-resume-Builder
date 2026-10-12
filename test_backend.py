import os
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import get_current_master_resume
from backend.services.fit_gate import evaluate_candidate_fit
from backend.services.jd_analyzer import analyze_job_description
from backend.services.tailoring_engine import run_tailoring_pipeline
from backend.services.docx_generator import generate_resume_docx, generate_cover_letter_docx
from backend.services.excel_tracker import get_all_applications, add_application
from backend.models.schemas import ApplicationRecord

def run_tests():
    print("=== 1. Testing Master Resume Loading ===")
    master = get_current_master_resume()
    assert master.contact.name == "Alex Mercer", f"Expected Alex Mercer, got {master.contact.name}"
    print(f"Master Resume Loaded: {master.contact.name}, {len(master.experience)} experiences, {len(master.skills)} skill categories.")

    print("\n=== 2. Testing Candidate Fit Gate (Matching JD) ===")
    matching_jd = """
    We are looking for a Senior Full-Stack Engineer with 5+ years of experience.
    Must have strong skills in Python, FastAPI, React, PostgreSQL, Docker, and AWS.
    Experience with event-driven systems and microservices is a plus.
    """
    res_match = evaluate_candidate_fit(master, matching_jd, "Senior Full-Stack Engineer", threshold=50)
    print(f"Fit Score: {res_match.fit_score}/100 | Passed: {res_match.passed} | Knockouts: {res_match.knockouts}")
    assert res_match.passed, "Matching JD should have cleared fit gate!"
    assert len(res_match.knockouts) == 0, "Expected 0 knockouts for matching JD!"
    print("MATCHING JD PASSED FIT GATE SUCCESSFULLY!")

    print("\n=== 3. Testing Candidate Fit Gate (Knockout: Clearance & Extreme Seniority) ===")
    knockout_jd = """
    Vice President of Engineering / CTO.
    Requires minimum 15+ years of software leadership experience managing 100+ engineers.
    Active Top Secret / SCI clearance with polygraph is mandatory.
    Candidate must possess active state Bar license.
    """
    res_ko = evaluate_candidate_fit(master, knockout_jd, "Vice President of Engineering", threshold=50)
    print(f"Fit Score: {res_ko.fit_score}/100 | Passed: {res_ko.passed} | Knockouts: {res_ko.knockouts}")
    assert not res_ko.passed, "Knockout JD should have failed fit gate!"
    assert len(res_ko.knockouts) > 0, "Knockout JD must detect knockouts!"
    print(f"Diagnostic Reason: {res_ko.reason}")
    print("KNOCKOUT JD SUCCESSFULLY DETECTED AND GATED!")

    print("\n=== 4. Testing JD Analysis ===")
    analysis = analyze_job_description(matching_jd, "Senior Full-Stack Engineer", "Acme Tech")
    print(f"Domain: {analysis.domain}")
    print(f"Seniority: {analysis.seniority_level}")
    print(f"Must-Haves: {analysis.must_have_skills}")
    print(f"Keywords: {analysis.keywords}")

    print("\n=== 5. Testing Tailoring Pipeline & Auto-Iteration Loop ===")
    tailored_resume, cover_letter, iterations, ats, hr = run_tailoring_pipeline(
        master_resume=master,
        jd=analysis,
        fit_gate=res_match,
        evidence_target=75,
        max_iterations=3
    )
    print(f"Iterations run: {len(iterations)}")
    for log in iterations:
        print(f"  - Iteration {log.iteration}: Evidence Match = {log.evidence_match_pct}%, ATS = {log.ats_score}, HR = {log.hr_score}")
    print(f"Final Evidence Match: {ats.evidence_match_pct}% (Target >= 75%)")
    assert ats.evidence_match_pct >= 75.0, f"Expected evidence match >= 75%, got {ats.evidence_match_pct}%"
    print(f"Final ATS Score: {ats.score}/100")
    print(f"Final HR Recruiter Score: {hr.score}/100 ({hr.quantified_impact_pct}% quantified metrics)")

    print("\n=== 6. Testing Production DOCX Generation ===")
    resume_file = generate_resume_docx(tailored_resume, filename_prefix="Test_Resume_Acme")
    cl_file = generate_cover_letter_docx(tailored_resume, cover_letter, filename_prefix="Test_CoverLetter_Acme")
    print(f"Generated DOCX files: {resume_file}, {cl_file}")
    assert os.path.exists(os.path.join("backend", "output", resume_file))
    assert os.path.exists(os.path.join("backend", "output", cl_file))

    print("\n=== 7. Testing Excel Tracker ===")
    test_record = ApplicationRecord(
        id="test_001",
        date="2026-10-12",
        company="Acme Tech",
        role="Senior Full-Stack Engineer",
        url="https://acme.tech/careers/123",
        fit_score=res_match.fit_score,
        gate_status="Cleared",
        ats_score=ats.score,
        hr_score=hr.score,
        evidence_match=ats.evidence_match_pct,
        resume_file=resume_file,
        cover_letter_file=cl_file,
        status="Ready",
        notes="Automated test application entry."
    )
    add_application(test_record)
    apps = get_all_applications()
    print(f"Total Applications in Excel: {len(apps)}")
    assert len(apps) >= 1
    print("EXCEL APPLICATION TRACKER RECORD VERIFIED!")

    print("\n>>> ALL BACKEND SERVICES AND HEURISTICS PASSED 100%! <<<")

if __name__ == "__main__":
    run_tests()
