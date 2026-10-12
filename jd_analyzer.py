import re
from typing import List, Dict, Any
from backend.models.schemas import JDAnalysis
from backend.services.fit_gate import extract_years_required

DOMAIN_KEYWORDS = {
    "Cloud & Infrastructure": ["aws", "azure", "gcp", "kubernetes", "k8s", "docker", "terraform", "devops", "cloud", "ci/cd", "infrastructure", "sre", "ansible"],
    "Full-Stack Web": ["react", "node", "typescript", "javascript", "fullstack", "full-stack", "frontend", "backend", "nextjs", "vue", "angular", "html", "css", "tailwind"],
    "FinTech & Payments": ["payment", "fintech", "banking", "ledger", "transactions", "pci", "trading", "compliance", "fraud", "financial"],
    "Data Engineering & Analytics": ["spark", "hadoop", "airflow", "snowflake", "etl", "data warehouse", "pipeline", "sql", "bigquery", "kafka"],
    "Distributed Systems & Backend": ["microservices", "distributed", "grpc", "rest", "concurrency", "scalability", "redis", "postgresql", "kafka", "rabbitmq"],
    "AI & Machine Learning": ["machine learning", "ml", "ai", "deep learning", "llm", "pytorch", "tensorflow", "nlp", "computer vision", "scikit-learn"]
}

SENIORITY_PATTERNS = [
    (r'\b(vp|vice president|chief|director|head of)\b', "Executive / Director"),
    (r'\b(principal|staff|distinguished|architect)\b', "Principal / Staff"),
    (r'\b(lead|senior|sr\.?|tech lead)\b', "Senior"),
    (r'\b(mid|intermediate)\b', "Mid-Level"),
    (r'\b(junior|jr\.?|associate|entry|graduate|intern)\b', "Entry / Junior")
]

TECH_KEYWORDS_CATALOG = [
    "python", "javascript", "typescript", "go", "golang", "java", "c++", "c#", "rust", "ruby", "php", "sql",
    "react", "angular", "vue", "next.js", "nextjs", "node.js", "node", "express", "fastapi", "django", "flask", "spring boot",
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform", "ci/cd", "github actions", "gitlab", "jenkins",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "kafka", "rabbitmq", "graphql", "rest api",
    "microservices", "system design", "distributed systems", "agile", "scrum", "tdd", "unit testing"
]

def analyze_job_description(jd_text: str, title: str = "", company: str = "") -> JDAnalysis:
    text_lower = jd_text.lower()
    combined = f"{title.lower()} {text_lower}"
    
    # 1. Determine Seniority
    seniority = "Mid-Level" # default
    for pat, label in SENIORITY_PATTERNS:
        if re.search(pat, combined):
            seniority = label
            break
            
    # 2. Determine Required Years
    req_years = extract_years_required(jd_text)
    if req_years == 0:
        if seniority == "Senior":
            req_years = 5
        elif seniority == "Principal / Staff":
            req_years = 8
        elif seniority == "Executive / Director":
            req_years = 10
        elif seniority == "Entry / Junior":
            req_years = 1
        else:
            req_years = 3

    # 3. Determine Primary Domain
    domain_scores: Dict[str, int] = {d: 0 for d in DOMAIN_KEYWORDS}
    for dom, kws in DOMAIN_KEYWORDS.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                domain_scores[dom] += 1
                
    sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
    primary_domain = sorted_domains[0][0] if sorted_domains and sorted_domains[0][1] > 0 else "Full-Stack Software Engineering"

    # 4. Extract Keywords & Skills
    found_tech = []
    for tech in TECH_KEYWORDS_CATALOG:
        if re.search(r'\b' + re.escape(tech) + r'\b', text_lower):
            found_tech.append(tech.title())

    # Split into must-haves vs nice-to-haves based on context sections
    must_haves = []
    nice_to_haves = []
    
    # Check for "preferred" or "nice to have" or "bonus" sections
    preferred_idx = -1
    for marker in ["preferred qualifications", "nice to have", "bonus points", "bonus qualifications", "what's a plus", "pluses"]:
        pos = text_lower.find(marker)
        if pos != -1 and (preferred_idx == -1 or pos < preferred_idx):
            preferred_idx = pos
            
    if preferred_idx != -1:
        req_section = text_lower[:preferred_idx]
        pref_section = text_lower[preferred_idx:]
        for tech in found_tech:
            t_lower = tech.lower()
            if t_lower in req_section:
                must_haves.append(tech)
            elif t_lower in pref_section:
                nice_to_haves.append(tech)
            else:
                must_haves.append(tech)
    else:
        # First 60% are must-haves, remainder nice-to-have
        split_point = max(3, int(len(found_tech) * 0.65))
        must_haves = found_tech[:split_point]
        nice_to_haves = found_tech[split_point:]

    if not must_haves and found_tech:
        must_haves = found_tech[:4]

    # 5. Extract Core Pain Points / Responsibilities
    pain_points = []
    bullet_matches = re.findall(r'(?:[-*•]|\d+\.)\s*([^\n\r]{20,150})', jd_text)
    for b in bullet_matches[:6]:
        b_clean = b.strip()
        if any(action in b_clean.lower() for action in ["design", "build", "scale", "architect", "lead", "implement", "optimize", "deliver", "collaborate", "ensure"]):
            pain_points.append(b_clean)
            
    if not pain_points:
        pain_points = [
            f"Deliver robust {primary_domain} solutions that scale reliably.",
            "Collaborate cross-functionally to streamline deployment pipelines and system performance.",
            "Write maintainable, well-tested code following best engineering practices."
        ]

    # 6. Concise Summary
    summary = (
        f"{seniority} position in {primary_domain} requiring ~{req_years}+ years of experience. "
        f"Core stack includes {', '.join(must_haves[:5]) if must_haves else 'modern software engineering tools'}. "
        f"Focuses on {pain_points[0].lower() if pain_points else 'scalable architecture'}."
    )

    return JDAnalysis(
        title=title or "Software Engineer",
        company=company or "Target Company",
        domain=primary_domain,
        seniority_level=seniority,
        required_years_experience=req_years,
        must_have_skills=must_haves,
        nice_to_have_skills=nice_to_haves,
        keywords=found_tech,
        pain_points=pain_points[:4],
        summary=summary
    )
