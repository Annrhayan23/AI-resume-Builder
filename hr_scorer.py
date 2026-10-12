import re
from typing import List, Dict, Any
from backend.models.schemas import MasterResume, JDAnalysis, HRScoreResult

POWER_ACTION_VERBS = {
    "architected", "spearheaded", "engineered", "orchestrated", "developed", "designed",
    "deployed", "implemented", "optimized", "streamlined", "accelerated", "scaled",
    "automated", "mentored", "refactored", "built", "launched", "constructed", "pioneered",
    "slashed", "increased", "boosted", "delivered", "transformed", "directed", "authored"
}

WEAK_OPENERS = {
    "responsible for", "assisted with", "helped", "worked on", "handled", "participated in",
    "tasked with", "duties included", "supported"
}

BUZZWORD_RED_FLAGS = {
    "guru", "ninja", "rockstar", "go-getter", "hard worker", "synergy", "think outside the box",
    "detail-oriented", "results-driven", "team player"
}

def analyze_bullet_metrics(bullet: str) -> bool:
    """Checks if bullet contains quantifiable metrics ($ / % / numbers / scale)."""
    # Matches patterns like 28%, $45,000, 10M+, 50k, 18 minutes, 99.99%, etc.
    patterns = [
        r'\b\d+(?:\.\d+)?%',
        r'\$\d+(?:,\d+)?(?:\.\d+)?[kmb]?',
        r'\b\d+(?:,\d+)?\+?\s*(?:million|billion|k|m|users|requests|events|clients|teams|hours|minutes|seconds|ms)\b',
        r'\b\d+\b'
    ]
    for pat in patterns:
        if re.search(pat, bullet, re.IGNORECASE):
            return True
    return False

def check_bullet_action_verb(bullet: str) -> bool:
    """Checks if the bullet starts with a power action verb."""
    words = bullet.strip().split()
    if not words:
        return False
    first_word = re.sub(r'[^a-zA-Z]', '', words[0]).lower()
    return first_word in POWER_ACTION_VERBS

def calculate_hr_score(resume: MasterResume, jd: JDAnalysis) -> HRScoreResult:
    all_bullets: List[str] = []
    for exp in resume.experience:
        all_bullets.extend(exp.bullets)
    for p in resume.projects:
        all_bullets.extend(p.bullets)
        
    total_bullets = max(1, len(all_bullets))
    
    # 1. Quantified Impact Metric
    quantified_count = sum(1 for b in all_bullets if analyze_bullet_metrics(b))
    quantified_pct = (quantified_count / total_bullets) * 100.0
    
    # 2. Action Verb Power Metric
    power_count = sum(1 for b in all_bullets if check_bullet_action_verb(b))
    power_verb_pct = (power_count / total_bullets) * 100.0
    
    # 3. Weak Openers & Red Flags Check
    detected_red_flags: List[str] = []
    for b in all_bullets:
        b_lower = b.lower()
        for weak in WEAK_OPENERS:
            if b_lower.startswith(weak):
                detected_red_flags.append(f"Passive opener: '{weak.title()}' in bullet.")
        for bw in BUZZWORD_RED_FLAGS:
            if re.search(r'\b' + re.escape(bw) + r'\b', b_lower):
                detected_red_flags.append(f"Overused cliché: '{bw}' detected.")
                
    detected_red_flags = list(dict.fromkeys(detected_red_flags))[:5] # Deduplicate

    # 4. Readability & Skim-Test
    avg_words = sum(len(b.split()) for b in all_bullets) / total_bullets
    if 15 <= avg_words <= 32:
        readability = "Exceptional (Clean 1-2 line executive scan)"
        readability_score = 95
    elif 10 <= avg_words < 15:
        readability = "Adequate (Slightly concise; consider adding business context)"
        readability_score = 80
    else:
        readability = "Dense (Bullets exceed 32 words; recommend tightening to avoid recruiter eye fatigue)"
        readability_score = 70

    # 5. Seniority Tone
    if jd.seniority_level in ["Senior", "Principal / Staff", "Executive / Director"]:
        leadership_words = {"architected", "spearheaded", "orchestrated", "mentored", "directed", "scaled", "pioneered"}
        has_leadership = any(any(lw in b.lower() for lw in leadership_words) for b in all_bullets)
        if has_leadership:
            seniority_tone = "Strong Senior/Strategic Authority"
            tone_score = 95
        else:
            seniority_tone = "Execution-Oriented (Needs stronger architectural ownership voice)"
            tone_score = 75
    else:
        seniority_tone = "Well-Calibrated Professional Delivery"
        tone_score = 90

    # Aggregate HR Score (0-100)
    # Weights: 35% Quantified Impact, 25% Action Verbs, 20% Readability, 20% Seniority Alignment
    raw_hr = (
        (0.35 * min(100, (quantified_pct / 70.0) * 100)) +
        (0.25 * min(100, (power_verb_pct / 80.0) * 100)) +
        (0.20 * readability_score) +
        (0.20 * tone_score)
    )
    
    # Penalize for red flags
    if detected_red_flags:
        raw_hr -= (len(detected_red_flags) * 3)
        
    final_score = max(30, min(98, int(round(raw_hr))))
    
    # Strengths & Recommendations
    strengths = []
    if quantified_pct >= 60:
        strengths.append(f"High outcome quantification ({round(quantified_pct)}% of bullets include metrics).")
    if power_verb_pct >= 70:
        strengths.append(f"Commanding action verbs ({round(power_verb_pct)}% start with decisive engineering verbs).")
    if not detected_red_flags:
        strengths.append("Zero passive openers or cliché fluff words detected.")
    if not strengths:
        strengths.append("Solid technical substance across all project experiences.")

    recommendations = []
    if quantified_pct < 65:
        recommendations.append("Enhance 1-2 additional bullets with measured business impact (%, latency, $, or scale).")
    if power_verb_pct < 75:
        recommendations.append("Ensure every single bullet opens with an active past-tense engineering verb.")
    if detected_red_flags:
        recommendations.append("Replace passive phrases with direct ownership verbs (e.g. 'Engineered' instead of 'Responsible for').")
    if not recommendations:
        recommendations.append("Format is fully dialed for executive recruiter screening.")

    summary = (
        f"Recruiter Evaluation: {final_score}/100. "
        f"{round(quantified_pct)}% quantified impact with {seniority_tone.lower()}. "
        f"{'Ready for high-tier hiring manager review.' if final_score >= 80 else 'Solid baseline with room for higher outcome metrics.'}"
    )

    return HRScoreResult(
        score=final_score,
        quantified_impact_pct=round(quantified_pct, 1),
        action_verb_power_pct=round(power_verb_pct, 1),
        seniority_tone_rating=seniority_tone,
        readability_rating=readability,
        red_flags=detected_red_flags,
        recruiter_summary=summary,
        strengths=strengths,
        recommendations=recommendations
    )
