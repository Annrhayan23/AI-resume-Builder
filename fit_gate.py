import re
from typing import List, Tuple, Set
from backend.models.schemas import MasterResume, FitGateResult

# Common tech aliases for canonical matching
TECH_ALIASES = {
    "react": ["reactjs", "react.js"],
    "node": ["nodejs", "node.js"],
    "typescript": ["ts"],
    "javascript": ["js"],
    "postgres": ["postgresql", "psql"],
    "fastapi": ["fast-api"],
    "k8s": ["kubernetes"],
    "aws": ["amazon web services"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "golang": ["go"],
}

def normalize_text(text: str) -> str:
    return re.sub(r'[^a-z0-9+#]', ' ', text.lower())

def extract_years_required(jd_text: str) -> int:
    """Finds requirements like '5+ years of experience', 'minimum 8 years', etc."""
    patterns = [
        r'(\d+)\+?\s*(?:-\s*\d+)?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+relevant|\s+professional|\s+software)?\s+experience',
        r'minimum\s+(?:of\s+)?(\d+)\s*(?:years?|yrs?)',
        r'at\s+least\s+(\d+)\s*(?:years?|yrs?)',
        r'(\d+)\s*(?:years?|yrs?)\s+minimum'
    ]
    years_found = []
    text_lower = jd_text.lower()
    for pat in patterns:
        matches = re.findall(pat, text_lower)
        for m in matches:
            try:
                years_found.append(int(m))
            except ValueError:
                pass
    if years_found:
        # Cap outliers to reasonable bounds
        valid_years = [y for y in years_found if 1 <= y <= 25]
        if valid_years:
            return max(valid_years)
    return 0

def estimate_candidate_years(master_resume: MasterResume) -> int:
    """Estimates candidate total years of professional experience from history."""
    if not master_resume.experience:
        return 3 # fallback baseline
    years_spanned = 0
    # Try parsing start dates
    min_year = 9999
    max_year = 2026
    found_dates = False
    for exp in master_resume.experience:
        if exp.start_date:
            m = re.search(r'(\d{4})', exp.start_date)
            if m:
                found_dates = True
                yr = int(m.group(1))
                if yr < min_year:
                    min_year = yr
    if found_dates and min_year < 9999:
        years_spanned = max(1, max_year - min_year)
    else:
        # Fallback count 2 years per experience entry
        years_spanned = max(2, len(master_resume.experience) * 2)
    return years_spanned

def detect_clearance_knockout(jd_text: str) -> List[str]:
    """Detects clearance or citizenship knockouts."""
    knockouts = []
    text_lower = jd_text.lower()
    if re.search(r'\b(active top secret|ts/sci|polygraph required|active secret clearance)\b', text_lower):
        knockouts.append("Mandatory active Government Security Clearance (TS/SCI/Polygraph) required by position.")
    if re.search(r'\b(must possess active bar license|licensed attorney|board certified physician)\b', text_lower):
        knockouts.append("Specialized professional state licensing (Bar/Medical Board) required.")
    return knockouts

def detect_seniority_knockout(candidate_years: int, jd_text: str, jd_title: str) -> List[str]:
    """Detects if candidate is applying for an executive/principal tier with severe experience shortfall."""
    knockouts = []
    combined = (jd_title + " " + jd_text[:500]).lower()
    
    is_executive = bool(re.search(r'\b(vice president|vp|director of engineering|head of engineering|chief technology officer|cto|c-level)\b', combined))
    is_principal = bool(re.search(r'\b(principal engineer|staff engineer|distinguished engineer|fellow)\b', combined))
    
    if is_executive and candidate_years < 7:
        knockouts.append(f"Executive/Director tier role requiring 10-15+ years leadership; candidate has ~{candidate_years} years.")
    elif is_principal and candidate_years < 4:
        knockouts.append(f"Principal/Staff tier role requiring 8-10+ years architectural leadership; candidate has ~{candidate_years} years.")
        
    return knockouts

def collect_candidate_skills(master_resume: MasterResume) -> Set[str]:
    """Aggregates all unique skills, tools, and technologies from master resume."""
    skills = set()
    # From skills map
    for category, skill_list in master_resume.skills.items():
        for s in skill_list:
            skills.add(s.lower().strip())
    # From experience technologies & bullets
    for exp in master_resume.experience:
        for t in exp.technologies:
            skills.add(t.lower().strip())
        for b in exp.bullets:
            # extract recognized words
            words = re.findall(r'[A-Za-z0-9+#]+', b.lower())
            for w in words:
                if len(w) >= 3:
                    skills.add(w)
    # From projects
    for proj in master_resume.projects:
        for t in proj.technologies:
            skills.add(t.lower().strip())
    # From certifications
    for cert in master_resume.certifications:
        skills.add(cert.lower().strip())
        
    return skills

def evaluate_candidate_fit(master_resume: MasterResume, jd_text: str, jd_title: str = "", threshold: int = 50) -> FitGateResult:
    """
    Candidate Fit Gate Evaluator:
    Strictly gates whether the master resume clears the fit bar against the JD.
    Zero hard knockouts allowed.
    """
    candidate_years = estimate_candidate_years(master_resume)
    required_years = extract_years_required(jd_text)
    
    knockouts: List[str] = []
    
    # Check 1: Mandatory clearances or medical/legal license
    knockouts.extend(detect_clearance_knockout(jd_text))
    
    # Check 2: Seniority tier deficit
    knockouts.extend(detect_seniority_knockout(candidate_years, jd_text, jd_title))
    
    # Check 3: Extreme experience deficit (>5 year shortfall)
    if required_years > 0 and (required_years - candidate_years) >= 5:
        knockouts.append(f"Job requires {required_years}+ years of experience; candidate profile indicates ~{candidate_years} years (deficit of {required_years - candidate_years} years).")

    # Extract candidate skills
    cand_skills = collect_candidate_skills(master_resume)
    
    # Extract JD technical tokens
    jd_normalized = normalize_text(jd_text + " " + jd_title)
    jd_tokens = set(re.findall(r'[a-z0-9+#]{2,}', jd_normalized))
    
    # Common stop words to exclude from tech evaluation
    stopwords = {
        "and", "the", "for", "with", "you", "that", "this", "will", "our", "are", "team", "work", "role",
        "have", "from", "your", "years", "skills", "experience", "working", "ability", "strong", "knowledge",
        "looking", "opportunity", "company", "requirements", "responsibilities", "qualifications", "preferred",
        "plus", "about", "what", "we", "can", "help", "build", "using", "more", "other", "such", "well",
        "must", "including", "across", "within", "high", "good", "great", "every", "part", "both", "join"
    }
    jd_tech_tokens = {t for t in jd_tokens if t not in stopwords and not t.isdigit() and len(t) >= 3}
    
    # Check skill overlap
    matched_skills = set()
    missing_skills = []
    
    for skill in cand_skills:
        skill_norm = skill.lower().strip()
        if skill_norm in jd_tokens or any(alias in jd_tokens for alias in TECH_ALIASES.get(skill_norm, [])):
            matched_skills.add(skill_norm)
            
    # Key technologies mentioned in JD
    key_jd_techs = [t for t in jd_tech_tokens if t in {
        "python", "javascript", "typescript", "java", "go", "golang", "c++", "c#", "rust", "ruby", "php", "swift",
        "react", "angular", "vue", "node", "django", "fastapi", "spring", "flask", "express", "nextjs",
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "linux", "ci/cd", "kafka", "redis",
        "sql", "postgresql", "mysql", "mongodb", "graphql", "rest", "microservices", "elasticsearch"
    }]
    
    if key_jd_techs:
        for tech in key_jd_techs:
            if tech not in cand_skills and not any(alias in cand_skills for alias in TECH_ALIASES.get(tech, [])):
                missing_skills.append(tech)
                
    # Calculate component scores
    # 1. Skill overlap score (0 - 50)
    if key_jd_techs:
        matched_key = [t for t in key_jd_techs if t in cand_skills or any(alias in cand_skills for alias in TECH_ALIASES.get(t, []))]
        skill_score = min(50.0, (len(matched_key) / max(1, len(key_jd_techs))) * 50.0)
    else:
        # Generic token overlap
        overlap = len(matched_skills)
        skill_score = min(50.0, (overlap / 10.0) * 50.0)
        
    # Check 4: Zero tech overlap knockout
    if key_jd_techs and len(matched_key) == 0 and len(matched_skills) < 2:
        knockouts.append(f"Zero transferable foundational technologies matched for role requiring: {', '.join(key_jd_techs[:4])}.")
        
    # 2. Experience score (0 - 30)
    if required_years > 0:
        ratio = min(1.0, candidate_years / required_years)
        exp_score = ratio * 30.0
    else:
        exp_score = 25.0
        
    # 3. Domain & baseline score (0 - 20)
    domain_score = 15.0 if len(matched_skills) >= 3 else 8.0
    
    # Aggregate raw fit score
    raw_score = int(round(skill_score + exp_score + domain_score))
    raw_score = max(5, min(100, raw_score))
    
    # If hard knockouts exist, penalize score and force fail
    if knockouts:
        fit_score = min(raw_score, threshold - 15)
        passed = False
    else:
        fit_score = raw_score
        passed = fit_score >= threshold
        
    # Construct diagnostic reason
    if passed:
        reason = f"Candidate cleared fit bar with score {fit_score}/100 (Threshold: {threshold}). Zero hard knockouts detected. Proceeding to in-depth JD analysis and truthful tailoring."
    else:
        if knockouts:
            reason = f"GATE HALT: Master resume triggered {len(knockouts)} hard knockout(s). Fit score capped at {fit_score}/100 (Threshold: {threshold}). Resume tailoring blocked: this tool strictly refuses to invent experience to bridge genuine qualification chasms."
        else:
            reason = f"GATE HALT: Fit score of {fit_score}/100 failed to clear the required bar of {threshold}/100. Key qualification gaps detected. Tailoring aborted to maintain resume veracity."
            
    remedies = []
    if missing_skills:
        remedies.append(f"Acquire hands-on project experience with: {', '.join(missing_skills[:5])}")
    if required_years > candidate_years:
        remedies.append(f"Role targets {required_years}+ years of experience; candidate currently has ~{candidate_years} years.")
    if not remedies:
        remedies.append("Consider targeting mid-tier roles aligned with existing cloud/fullstack stack.")

    return FitGateResult(
        passed=passed,
        fit_score=fit_score,
        threshold=threshold,
        knockouts=knockouts,
        reason=reason,
        missing_qualifications=missing_skills[:8],
        domain_match_score=round(skill_score, 1),
        experience_match_score=round(exp_score, 1),
        actionable_remedies=remedies
    )
