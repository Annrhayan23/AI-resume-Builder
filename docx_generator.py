import os
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

from backend.config import OUTPUT_DIR
from backend.models.schemas import MasterResume, JDAnalysis

NAVY_BLUE = RGBColor(30, 58, 138)       # #1E3A8A
CHARCOAL = RGBColor(31, 41, 55)        # #1F2937
MUTED_GRAY = RGBColor(107, 114, 128)    # #6B7280

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_section_divider(doc, heading_text: str):
    """Adds a bold section heading with a bottom border line."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    
    run = p.add_run(heading_text.upper())
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = NAVY_BLUE
    
    # Add bottom horizontal border to paragraph
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(r'<w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                     r'<w:bottom w:val="single" w:sz="6" w:space="1" w:color="1E3A8A"/>'
                     r'</w:pBdr>')
    pPr.append(pBdr)

def generate_resume_docx(resume: MasterResume, filename_prefix: str = "Tailored_Resume") -> str:
    """Generates a production-grade, ATS-parseable DOCX resume."""
    doc = Document()
    
    # Set page margins (0.6 inches for modern executive density)
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.6)
        s.bottom_margin = Inches(0.6)
        s.left_margin = Inches(0.65)
        s.right_margin = Inches(0.65)
        
    # --- Header ---
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    name_run = title_p.add_run(resume.contact.name or "Alex Mercer")
    name_run.font.name = 'Calibri'
    name_run.font.size = Pt(20)
    name_run.font.bold = True
    name_run.font.color.rgb = NAVY_BLUE
    
    # Contact line
    contact_parts = []
    if resume.contact.email:
        contact_parts.append(resume.contact.email)
    if resume.contact.phone:
        contact_parts.append(resume.contact.phone)
    if resume.contact.location:
        contact_parts.append(resume.contact.location)
    if resume.contact.linkedin:
        contact_parts.append(resume.contact.linkedin.replace("https://", ""))
    if resume.contact.github:
        contact_parts.append(resume.contact.github.replace("https://", ""))
        
    contact_p = doc.add_paragraph()
    contact_p.paragraph_format.space_after = Pt(8)
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_run = contact_p.add_run("  |  ".join(contact_parts))
    c_run.font.name = 'Calibri'
    c_run.font.size = Pt(9.5)
    c_run.font.color.rgb = MUTED_GRAY

    # --- Professional Summary ---
    if resume.summary:
        add_section_divider(doc, "Professional Summary")
        sum_p = doc.add_paragraph()
        sum_p.paragraph_format.space_after = Pt(6)
        sum_p.paragraph_format.line_spacing = 1.15
        s_run = sum_p.add_run(resume.summary)
        s_run.font.name = 'Calibri'
        s_run.font.size = Pt(10)
        s_run.font.color.rgb = CHARCOAL

    # --- Technical Skills ---
    if resume.skills:
        add_section_divider(doc, "Core Competencies & Technical Skills")
        for category, skill_list in resume.skills.items():
            sp = doc.add_paragraph()
            sp.paragraph_format.space_before = Pt(1)
            sp.paragraph_format.space_after = Pt(2)
            cat_run = sp.add_run(f"•  {category}: ")
            cat_run.font.name = 'Calibri'
            cat_run.font.size = Pt(9.5)
            cat_run.font.bold = True
            cat_run.font.color.rgb = CHARCOAL
            
            val_run = sp.add_run(", ".join(skill_list))
            val_run.font.name = 'Calibri'
            val_run.font.size = Pt(9.5)
            val_run.font.color.rgb = CHARCOAL

    # --- Professional Experience ---
    if resume.experience:
        add_section_divider(doc, "Professional Experience")
        for exp in resume.experience:
            # Job Title & Company + Dates line
            exp_p = doc.add_paragraph()
            exp_p.paragraph_format.space_before = Pt(6)
            exp_p.paragraph_format.space_after = Pt(2)
            exp_p.paragraph_format.keep_with_next = True
            
            role_run = exp_p.add_run(exp.role)
            role_run.font.name = 'Calibri'
            role_run.font.size = Pt(10.5)
            role_run.font.bold = True
            role_run.font.color.rgb = NAVY_BLUE
            
            sep_run = exp_p.add_run("  —  ")
            sep_run.font.name = 'Calibri'
            sep_run.font.size = Pt(10)
            sep_run.font.color.rgb = MUTED_GRAY
            
            comp_run = exp_p.add_run(exp.company)
            comp_run.font.name = 'Calibri'
            comp_run.font.size = Pt(10)
            comp_run.font.bold = True
            comp_run.font.color.rgb = CHARCOAL
            
            date_str = f"  ({exp.start_date} - {exp.end_date if not exp.current else 'Present'})"
            if exp.location:
                date_str += f" | {exp.location}"
            date_run = exp_p.add_run(date_str)
            date_run.font.name = 'Calibri'
            date_run.font.size = Pt(9)
            date_run.font.italic = True
            date_run.font.color.rgb = MUTED_GRAY

            # Bullets
            for bullet in exp.bullets:
                bp = doc.add_paragraph(style='List Bullet')
                bp.paragraph_format.space_before = Pt(1)
                bp.paragraph_format.space_after = Pt(2)
                bp.paragraph_format.line_spacing = 1.12
                b_run = bp.add_run(bullet)
                b_run.font.name = 'Calibri'
                b_run.font.size = Pt(9.5)
                b_run.font.color.rgb = CHARCOAL

    # --- Projects ---
    if resume.projects:
        add_section_divider(doc, "Key Projects & Open Source")
        for proj in resume.projects:
            pp = doc.add_paragraph()
            pp.paragraph_format.space_before = Pt(4)
            pp.paragraph_format.space_after = Pt(1)
            p_name = pp.add_run(proj.name)
            p_name.font.name = 'Calibri'
            p_name.font.size = Pt(10)
            p_name.font.bold = True
            p_name.font.color.rgb = NAVY_BLUE
            
            if proj.technologies:
                t_run = pp.add_run(f"  [{', '.join(proj.technologies)}]")
                t_run.font.name = 'Calibri'
                t_run.font.size = Pt(8.5)
                t_run.font.italic = True
                t_run.font.color.rgb = MUTED_GRAY

            if proj.description:
                dp = doc.add_paragraph()
                dp.paragraph_format.space_after = Pt(2)
                dp_run = dp.add_run(proj.description)
                dp_run.font.name = 'Calibri'
                dp_run.font.size = Pt(9.5)
                dp_run.font.color.rgb = CHARCOAL

            for b in proj.bullets:
                pbp = doc.add_paragraph(style='List Bullet')
                pbp.paragraph_format.space_after = Pt(1)
                pbp_run = pbp.add_run(b)
                pbp_run.font.name = 'Calibri'
                pbp_run.font.size = Pt(9.5)
                pbp_run.font.color.rgb = CHARCOAL

    # --- Education & Certifications ---
    if resume.education or resume.certifications:
        add_section_divider(doc, "Education & Certifications")
        for edu in resume.education:
            ep = doc.add_paragraph()
            ep.paragraph_format.space_after = Pt(2)
            deg_run = ep.add_run(f"{edu.degree}  —  {edu.institution}")
            deg_run.font.name = 'Calibri'
            deg_run.font.size = Pt(9.5)
            deg_run.font.bold = True
            deg_run.font.color.rgb = CHARCOAL
            
            extra = []
            if edu.graduation_year:
                extra.append(edu.graduation_year)
            if edu.gpa:
                extra.append(f"GPA: {edu.gpa}")
            if edu.honors:
                extra.append(edu.honors)
            if extra:
                e_extra = ep.add_run(f" ({', '.join(extra)})")
                e_extra.font.name = 'Calibri'
                e_extra.font.size = Pt(9)
                e_extra.font.italic = True
                e_extra.font.color.rgb = MUTED_GRAY

        if resume.certifications:
            cp = doc.add_paragraph()
            cp.paragraph_format.space_after = Pt(2)
            c_label = cp.add_run("Certifications: ")
            c_label.font.name = 'Calibri'
            c_label.font.size = Pt(9.5)
            c_label.font.bold = True
            c_label.font.color.rgb = CHARCOAL
            c_text = cp.add_run(", ".join(resume.certifications))
            c_text.font.name = 'Calibri'
            c_text.font.size = Pt(9.5)
            c_text.font.color.rgb = CHARCOAL

    clean_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', filename_prefix)
    out_path = OUTPUT_DIR / f"{clean_prefix}.docx"
    doc.save(str(out_path))
    return f"{clean_prefix}.docx"

def generate_cover_letter_docx(resume: MasterResume, letter_content: str, filename_prefix: str = "Cover_Letter") -> str:
    """Generates a professional DOCX cover letter matching resume styling."""
    doc = Document()
    
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    # Header
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(2)
    name_run = title_p.add_run(resume.contact.name or "Alex Mercer")
    name_run.font.name = 'Calibri'
    name_run.font.size = Pt(18)
    name_run.font.bold = True
    name_run.font.color.rgb = NAVY_BLUE

    contact_parts = []
    if resume.contact.email:
        contact_parts.append(resume.contact.email)
    if resume.contact.phone:
        contact_parts.append(resume.contact.phone)
    if resume.contact.location:
        contact_parts.append(resume.contact.location)
    if resume.contact.linkedin:
        contact_parts.append(resume.contact.linkedin.replace("https://", ""))
        
    contact_p = doc.add_paragraph()
    contact_p.paragraph_format.space_after = Pt(12)
    c_run = contact_p.add_run("  |  ".join(contact_parts))
    c_run.font.name = 'Calibri'
    c_run.font.size = Pt(9.5)
    c_run.font.color.rgb = MUTED_GRAY

    # Divider line
    pPr = contact_p._p.get_or_add_pPr()
    pBdr = parse_xml(r'<w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                     r'<w:bottom w:val="single" w:sz="6" w:space="1" w:color="1E3A8A"/>'
                     r'</w:pBdr>')
    pPr.append(pBdr)

    # Body paragraphs
    paragraphs = letter_content.strip().split("\n\n")
    for para in paragraphs:
        if not para.strip():
            continue
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(10)
        p.paragraph_format.line_spacing = 1.2
        r = p.add_run(para.strip())
        r.font.name = 'Calibri'
        r.font.size = Pt(10.5)
        r.font.color.rgb = CHARCOAL

    clean_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', filename_prefix)
    out_path = OUTPUT_DIR / f"{clean_prefix}.docx"
    doc.save(str(out_path))
    return f"{clean_prefix}.docx"
