import re
from typing import List, Dict, Set
from backend.models.schemas import MasterResume, JDAnalysis, ATSScoreResult
from backend.services.fit_gate import TECH_ALIASES

def collect_resume_text(resume: MasterResume) -> Dict[str, str]:
    """Extracts text separated by sections."""
    summary_text = resume.summary
    skills_text = " ".join([f"{cat} " + " ".join(s_list) for cat, s_list in resume.skills.items()])
    
    exp_bullets = []
    for exp in resume.experience:
        exp_bullets.extend(exp.bullets)
        exp_bullets.extend(exp.technologies)
    exp_text = " ".join(exp_bullets)
    
    proj_bullets = []
    for p in resume.projects:
        proj_bullets.append(p.name)
        proj_bullets.append(p.description)
        proj_bullets.extend(p.bullets)
        proj_bullets.extend(p.technologies)
    proj_text = " ".join(proj_bullets)
    
    all_text = f"{summary_text} {skills_text} {exp_text} {proj_text}".lower()
    
    return {
        "summary": summary_text.lower(),
        "skills": skills_text.lower(),
        "experience": exp_text.lower(),
        "projects": proj_text.lower(),
        "combined": all_text
    }

def check_keyword_in_text(kw: str, text: str) -> bool:
    kw_norm = kw.lower().strip()
    if re.search(r'\b' + re.escape(kw_norm) + r'\b', text):
        return True
    # Check aliases
    for alias in TECH_ALIASES.get(kw_norm, []):
        if re.search(r'\b' + re.escape(alias) + r'\b', text):
            return True
    return False

def calculate_ats_score(resume: MasterResume, jd: JDAnalysis) -> ATSScoreResult:
    sections = collect_resume_text(resume)
    all_text = sections["combined"]
    exp_and_proj_text = f"{sections['experience']} {sections['projects']}"
    
    target_kws = jd.keywords if jd.keywords else ["Software Engineering", "Problem Solving"]
    must_haves = jd.must_have_skills if jd.must_have_skills else target_kws[:3]
    
    matched_kws = []
    missing_kws = []
    
    for kw in target_kws:
        if check_keyword_in_text(kw, all_text):
            matched_kws.append(kw)
        else:
            missing_kws.append(kw)
            
    kw_rate = (len(matched_kws) / max(1, len(target_kws))) * 100.0
    
    # Calculate Evidence Match %
    # Must-have skills MUST have demonstrable evidence in Experience or Project bullets!
    must_haves_with_evidence = []
    for mh in must_haves:
        if check_keyword_in_text(mh, exp_and_proj_text):
            must_haves_with_evidence.append(mh)
            
    evidence_match_pct = (len(must_haves_with_evidence) / max(1, len(must_haves))) * 100.0
    
    # Section breakdowns
    summary_matches = sum(1 for kw in target_kws if check_keyword_in_text(kw, sections["summary"]))
    skills_matches = sum(1 for kw in target_kws if check_keyword_in_text(kw, sections["skills"]))
    exp_matches = sum(1 for kw in target_kws if check_keyword_in_text(kw, sections["experience"]))
    
    sec_scores = {
        "summary_alignment": min(100, int((summary_matches / max(1, len(target_kws) * 0.4)) * 100)),
        "skills_coverage": min(100, int((skills_matches / max(1, len(target_kws) * 0.7)) * 100)),
        "experience_depth": min(100, int((exp_matches / max(1, len(target_kws) * 0.6)) * 100)),
        "must_have_evidence": int(round(evidence_match_pct))
    }
    
    # Overall ATS Score heuristic
    # 40% Evidence match, 40% Overall Keyword coverage, 20% Section distribution
    raw_ats = (0.40 * evidence_match_pct) + (0.40 * kw_rate) + (0.20 * min(100, (exp_matches * 15)))
    overall_score = max(20, min(99, int(round(raw_ats))))
    
    advisory_notes = []
    if evidence_match_pct >= 75:
        advisory_notes.append(f"Strong evidence match ({round(evidence_match_pct)}%): Core required skills are verified in work bullets.")
    else:
        advisory_notes.append(f"Evidence match at {round(evidence_match_pct)}%: Bring under-emphasized must-have competencies into active bullet context.")
        
    if missing_kws:
        advisory_notes.append(f"Missing terminology to incorporate if applicable: {', '.join(missing_kws[:4])}.")
    else:
        advisory_notes.append("Optimal keyword coverage achieved across core competencies.")
        
    return ATSScoreResult(
        score=overall_score,
        keyword_match_rate=round(kw_rate, 1),
        evidence_match_pct=round(evidence_match_pct, 1),
        missing_keywords=missing_kws[:8],
        matched_keywords=matched_kws,
        section_scores=sec_scores,
        formatting_passed=True,
        advisory_notes=advisory_notes
    )
