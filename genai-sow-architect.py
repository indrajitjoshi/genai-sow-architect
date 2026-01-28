import streamlit as st
from datetime import date
import io
import re
import os
import time 
import requests
import pandas as pd

# --- FILE PATHING & DIAGRAM MAPPING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "diagrams")

# Static assets for the cover page
AWS_PN_LOGO = os.path.join(ASSETS_DIR, "aws partner logo.jpg")
ONETURE_LOGO = os.path.join(ASSETS_DIR, "oneture logo1.jpg")
AWS_ADV_LOGO = os.path.join(ASSETS_DIR, "aws advanced logo1.jpg")

# Mapped Infra Costs for Section 4
SOW_COST_TABLE_MAP = { 
    "L1 Support Bot POC SOW": { "POC": "3,536.40 USD" }, 
    "Beauty Advisor POC SOW": { 
        "POC": "1,213.04 USD + 100 USD (Amazon Bedrock Cost) = 1,313.04 USD", 
        "Production": "1,213.04 USD + 2,970.06 (Amazon Bedrock Cost) = 4,183.1 USD" 
    }, 
    "Ready Search POC Scope of Work Document":{ "POC": "2,641.40 USD" }, 
    "AI based Image Enhancement POC SOW": { "POC": "2,814.34 USD" }, 
    "AI based Image Inspection POC SOW": { "POC": "3,536.40 USD" }, 
    "Gen AI for SOP POC SOW": { "POC": "2,110.30 USD" }, 
    "Project Scope Document": { "Production": "2,993.60 USD" }, 
    "Gen AI Speech To Speech": { "Production": "2,124.23 USD" }, 
    "PoC Scope Document": { "PoC": "$ 3,150 (Incl. 1,000 USD Bedrock)" }
}

# AWS Calculator Links for Section 4
CALCULATOR_LINKS = {
    "L1 Support Bot POC SOW": "https://calculator.aws/#/estimate?id=211ea64cba5a8f5dc09805f4ad1a1e598ef5238b",
    "Ready Search POC Scope of Work Document": "https://calculator.aws/#/estimate?id=f8bc48f1ae566b8ea1241994328978e7e86d3490",
    "AI based Image Enhancement POC SOW": "https://calculator.aws/#/estimate?id=9a3e593b92b796acecf31a78aec17d7eb957d1e5",
    "Beauty Advisor POC SOW": "https://calculator.aws/#/estimate?id=3f89756a35f7bac7b2cd88d95f3e9aba9be9b0eb",
    "AI based Image Inspection POC SOW": "https://calculator.aws/#/estimate?id=72c56f93b0c0e101d67a46af4f4fe9886eb93342",
    "Gen AI for SOP POC SOW": "https://calculator.aws/#/estimate?id=c21e9b242964724bf83556cfeee821473bb935d1",
    "Project Scope Document": "https://calculator.aws/#/estimate?id=37339d6e34c73596559fe09ca16a0ac2ec4c4252",
    "Gen AI Speech To Speech": "https://calculator.aws/#/estimate?id=8444ae26e6d61e5a43e8e743578caa17fd7f3e69",
    "PoC Scope Document": "https://calculator.aws/#/estimate?id=420ed9df095e7824a144cb6c0e9db9e7ec3c4153"
}

# Architecture Diagram Mapping for Section 4
SOW_DIAGRAM_MAP = {
    "L1 Support Bot POC SOW": os.path.join(ASSETS_DIR, "L1 Support Bot POC SOW.png"),
    "Beauty Advisor POC SOW": os.path.join(ASSETS_DIR, "Beauty Advisor POC SOW.png"),
    "Ready Search POC Scope of Work Document": os.path.join(ASSETS_DIR, "Ready Search POC Scope of Work Document.png"),
    "AI based Image Enhancement POC SOW": os.path.join(ASSETS_DIR, "AI based Image Enhancement POC SOW.png"),
    "AI based Image Inspection POC SOW": os.path.join(ASSETS_DIR, "AI based Image Inspection POC SOW.png"),
    "Gen AI for SOP POC SOW": os.path.join(ASSETS_DIR, "Gen AI for SOP POC SOW.png"),
    "Project Scope Document": os.path.join(ASSETS_DIR, "Project Scope Document.png"),
    "Gen AI Speech To Speech": os.path.join(ASSETS_DIR, "Gen AI Speech To Speech.png"),
    "PoC Scope Document": os.path.join(ASSETS_DIR, "PoC Scope Document.png")
}

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="GenAI SOW Architect", layout="wide", page_icon="📄")

# Professional Styling for UI
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stakeholder-header { 
        background-color: #f1f5f9; padding: 8px 12px; border-radius: 6px; 
        margin-top: 10px; font-weight: bold; border-left: 4px solid #3b82f6;
    }
    .sow-preview {
        background-color: white; padding: 40px; border-radius: 12px;
        border: 1px solid #e2e8f0; line-height: 1.7; 
        color: #000000;
        font-family: "Times New Roman", Times, serif;
    }
    .sow-preview a { color: #0000EE; text-decoration: underline; }
    </style>
    """, unsafe_allow_html=True)

# --- WORD GENERATION HELPERS ---
def add_hyperlink(paragraph, text, url):
    from docx.oxml.shared import qn, OxmlElement
    import docx.opc.constants
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id, )
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    c = OxmlElement('w:color'); c.set(qn('w:val'), '0000EE') 
    u = OxmlElement('w:u'); u.set(qn('w:val'), 'single')
    rPr.append(c); rPr.append(u); new_run.append(rPr)
    t = OxmlElement('w:t'); t.text = text
    new_run.append(t); hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

def create_docx_logic(text_content, branding, sow_name):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)
    
    # PAGE 1: COVER
    p = doc.add_paragraph()
    if os.path.exists(AWS_PN_LOGO): doc.add_picture(AWS_PN_LOGO, width=Inches(1.6))
    doc.add_paragraph("\n" * 3)
    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = t.add_run(branding['sow_name']); run.font.size = Pt(26); run.bold = True
    stitle = doc.add_paragraph(); stitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    stitle.add_run("Scope of Work Document").font.size = Pt(14)
    doc.add_paragraph("\n" * 4)
    
    l_table = doc.add_table(rows=1, cols=3); l_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if branding.get("customer_logo_bytes"):
        l_table.rows[0].cells[0].paragraphs[0].add_run().add_picture(io.BytesIO(branding["customer_logo_bytes"]), width=Inches(1.5))
    if os.path.exists(ONETURE_LOGO):
        l_table.rows[0].cells[1].paragraphs[0].add_run().add_picture(ONETURE_LOGO, width=Inches(1.8))
    if os.path.exists(AWS_ADV_LOGO):
        l_table.rows[0].cells[2].paragraphs[0].add_run().add_picture(AWS_ADV_LOGO, width=Inches(1.5))
    
    doc.add_paragraph("\n" * 3)
    dt = doc.add_paragraph(); dt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    dt.add_run(branding["doc_date_str"]).bold = True
    doc.add_page_break()

    # OUTPUT SECTION MAPPING (STRICT 1-5 Numbering as requested)
    headers_map = {
        "1": "TABLE OF CONTENTS", 
        "2": "PROJECT OVERVIEW", 
        "3": "SCOPE OF WORK - TECHNICAL PROJECT PLAN",
        "4": "SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM", 
        "5": "RESOURCES & COST ESTIMATES"
    }

    lines = text_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line: i += 1; continue
        
        clean_line = re.sub(r'#+\s*', '', line).strip()
        upper = clean_line.upper()

        current_id = None
        for h_id, h_title in headers_map.items():
            if re.match(rf"^{h_id}[\.\s]+{re.escape(h_title)}", upper):
                current_id = h_id; break
        
        if current_id:
            if current_id != "1": doc.add_page_break()
            h = doc.add_heading(clean_line.upper(), level=1)
            for run in h.runs: 
                run.font.name = 'Times New Roman'
                run.font.color.rgb = RGBColor(0, 0, 0)
            
            # Injection Logic for Section 4 (Architectural Diagram Placement)
            if current_id == "4":
                diag = SOW_DIAGRAM_MAP.get(sow_name)
                if diag and os.path.exists(diag):
                    doc.add_paragraph("\n")
                    doc.add_picture(diag, width=Inches(5.8))
                    p_cap = doc.add_paragraph(f"{sow_name} – Architecture Diagram")
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    doc.add_paragraph("\n")
            i += 1; continue
            
        # Table Parsing Logic
        if line.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i]); i += 1
            if len(table_lines) >= 3:
                cols = [c.strip() for c in table_lines[0].split('|') if c.strip()]
                t_obj = doc.add_table(rows=1, cols=len(cols)); t_obj.style = "Table Grid"
                for idx, h_text in enumerate(cols):
                    cell = t_obj.rows[0].cells[idx]
                    r_h = cell.paragraphs[0].add_run(h_text)
                    r_h.bold = True; r_h.font.name = 'Times New Roman'
                for row_line in table_lines[2:]:
                    cells_data = [c.strip() for c in row_line.split('|') if c.strip()]
                    r_cells = t_obj.add_row().cells
                    for idx, c_text in enumerate(cells_data):
                        if idx < len(r_cells):
                            p_r = r_cells[idx].paragraphs[0]
                            # Detect "link" placeholder to add AWS Calculator Hyperlink in Section 4
                            if "link" in c_text.lower():
                                add_hyperlink(p_r, "AWS Cost Calculator Link", CALCULATOR_LINKS.get(sow_name, "https://calculator.aws/"))
                            else:
                                run_cell = p_r.add_run(c_text)
                                run_cell.font.name = 'Times New Roman'
            continue

        if line.startswith('## '):
            h = doc.add_heading(clean_line, level=2)
            for run in h.runs: run.font.color.rgb = RGBColor(0, 0, 0); run.font.name = 'Times New Roman'
        elif line.startswith('### '):
            h = doc.add_heading(clean_line, level=3)
            for run in h.runs: run.font.color.rgb = RGBColor(0, 0, 0); run.font.name = 'Times New Roman'
        elif line.startswith('- ') or line.startswith('* '):
            p_b = doc.add_paragraph(style="List Bullet")
            p_b.add_run(re.sub(r'^[\-\*]\s*', '', line)).font.name = 'Times New Roman'
        else:
            p_n = doc.add_paragraph()
            p_n.add_run(clean_line).font.name = 'Times New Roman'
        i += 1
        
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def call_gemini_with_retry(payload, api_key_input=""):
    apiKey = api_key_input if api_key_input else ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={apiKey}"
    delays = [1, 2, 4]
    for attempt in range(len(delays)):
        try:
            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200: return res, None
            if res.status_code in [503, 429]: time.sleep(delays[attempt]); continue
            return None, f"API Error {res.status_code}: {res.text}"
        except Exception: time.sleep(delays[attempt])
    return None, "API Overloaded."

# --- INITIALIZATION & DEFAULT STATES ---
def init_state():
    if 'generated_sow' not in st.session_state: st.session_state.generated_sow = ""
    if 'stakeholders' not in st.session_state:
        st.session_state.stakeholders = {
            "Partner": pd.DataFrame([{"Name": "Gaurav Kankaria", "Title": "Head of Analytics & ML", "Email": "gaurav.kankaria@oneture.com"}]),
            "Customer": pd.DataFrame([{"Name": "Prabhjot Singh", "Title": "Marketing Manager", "Email": "prabhjot.singh5@jublfood.com"}]),
            "AWS": pd.DataFrame([{"Name": "Anubhav Sood", "Title": "AWS Account Executive", "Email": "anbhsood@amazon.com"}]),
            "Escalation": pd.DataFrame([{"Name": "Omkar Dhavalikar", "Title": "AI/ML Lead", "Email": "omkar.dhavalikar@oneture.com"}])
        }
    if 'timeline_phases' not in st.session_state:
        st.session_state.timeline_phases = pd.DataFrame([
            {"Phase": "Infrastructure Setup", "Task": "Setup required AWS Services & gather documents", "Wk1": "X", "Wk2": "", "Wk3": "", "Wk4": ""},
            {"Phase": "Create Core Workflows", "Task": "Banner Upload & Validation Flow / Compliance Flow", "Wk1": "X", "Wk2": "", "Wk3": "", "Wk4": ""},
            {"Phase": "Backend Components", "Task": "Build Compliance Engine & Tagging Module", "Wk1": "", "Wk2": "X", "Wk3": "X", "Wk4": "X"},
            {"Phase": "Feedback & Testing", "Task": "Test and Validate compliance accuracy vs manual results", "Wk1": "", "Wk2": "", "Wk3": "", "Wk4": "X"}
        ])

init_state()

def reset_all():
    for key in list(st.session_state.keys()): del st.session_state[key]
    init_state(); st.rerun()

# --- INPUT SECTION (PRESERVED) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("Architect Pro")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    st.header("📋 1. Project Intake")
    sow_opts = list(SOW_DIAGRAM_MAP.keys())
    solution_type = st.selectbox("1.1 Solution Type", sow_opts)
    sow_key = solution_type
    engagement_type = st.selectbox("1.2 Engagement Type", ["Proof of Concept (PoC)", "Pilot", "MVP", "Production"])
    industry_type = st.selectbox("1.3 Industry", ["Retail", "BFSI", "Manufacturing", "Other"])
    funding_src = st.selectbox("1.4 Funding Ownership", ["Jointly Funded by AWS & Oneture", "AWS Only", "Customer Funded", "Partner Only"])
    if st.button("🗑️ Reset All", use_container_width=True): reset_all()

# --- MAIN UI INPUTS (PRESERVED) ---
st.title("🚀 GenAI SOW Architect")
st.header("📸 1. Branding & Project Cover")
col_cov1, col_cov2 = st.columns(2)
with col_cov1: customer_logo = st.file_uploader("Upload Customer Logo", type=["png", "jpg", "jpeg"])
with col_cov2: doc_date = st.date_input("Document Date", date.today())

st.header("📄 2. Project Overview Inputs")
biz_objective = st.text_area("2.1 Business Objective", placeholder="Example: Development of a Gen AI based solution to automate compliance checks...", height=100)
st.subheader("2.2 Stakeholders")
st.session_state.stakeholders["Partner"] = st.data_editor(st.session_state.stakeholders["Partner"], use_container_width=True, key="ed_p")
st.session_state.stakeholders["Customer"] = st.data_editor(st.session_state.stakeholders["Customer"], use_container_width=True, key="ed_c")
st.session_state.stakeholders["AWS"] = st.data_editor(st.session_state.stakeholders["AWS"], use_container_width=True, key="ed_a")
st.session_state.stakeholders["Escalation"] = st.data_editor(st.session_state.stakeholders["Escalation"], use_container_width=True, key="ed_e")

st.subheader("2.3 Assumptions & Dependencies")
deps = st.text_area("Key assumptions and dependencies", "Sample data provided by customer, AWS access provided, SME availability for validation...")
st.subheader("2.4 Success Criteria")
success = st.text_area("PoC Success Metrics", "Accuracy > 85% compared to manual review, Latency < 2s...")

st.header("📅 3. Technical Project Plan Inputs")
st.session_state.timeline_phases = st.data_editor(st.session_state.timeline_phases, num_rows="dynamic", use_container_width=True, key="ed_t")

st.header("💰 5. Resources & Cost Estimates")
res_cost_input = st.text_area("Additional Funding Details", f"The Project is {funding_src} as a 1-time investment to demonstrate capabilities of AWS and Oneture services.")

# --- OUTPUT GENERATION LOGIC (RESTRUCTURED) ---
if st.button("✨ Generate Professional SOW", type="primary", use_container_width=True):
    with st.spinner("Processing document sequence..."):
        def get_md(df): return df.to_markdown(index=False)
        cost_info = SOW_COST_TABLE_MAP.get(sow_key, {"POC": "TBD"})
        cost_table = "| System | Infra Cost | AWS Cost Calculator Link |\n| --- | --- | --- |\n"
        for k, v in cost_info.items():
            cost_table += f"| {k} | {v} | link |\n"
        
        prompt = f"""
        Generate a formal enterprise SOW. Follow this EXACT numbering for sections:

        # 1 TABLE OF CONTENTS
        1. Table of Contents
        2. Project Overview
        3. Scope of Work - Technical Project Plan
        4. Solution Architecture / Architectural Diagram
        5. Resources & Cost Estimates

        # 2 PROJECT OVERVIEW
        ## 2.1 OBJECTIVE
        {biz_objective}
        ## 2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM
        ### Partner Executive Sponsor
        {get_md(st.session_state.stakeholders["Partner"])}
        ### Customer Executive Sponsor
        {get_md(st.session_state.stakeholders["Customer"])}
        ### AWS Executive Sponsor
        {get_md(st.session_state.stakeholders["AWS"])}
        ### Project Escalation Contacts
        {get_md(st.session_state.stakeholders["Escalation"])}
        ## 2.3 ASSUMPTIONS & DEPENDENCIES
        {deps}
        ## 2.4 PROJECT SUCCESS CRITERIA
        {success}

        # 3 SCOPE OF WORK - TECHNICAL PROJECT PLAN
        (Use the following timeline data to generate a markdown table)
        {get_md(st.session_state.timeline_phases)}
        POC would be demoed iteratively for all the workflows across the 4 weeks of the POC.

        # 4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM
        (Architecture diagram image will be placed here)
        ## Infrastructure Cost Breakdown Basis POC
        {cost_table}

        # 5 RESOURCES & COST ESTIMATES
        {res_cost_input}
        """
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res, err = call_gemini_with_retry(payload, api_key)
        if res:
            st.session_state.generated_sow = res.json()['candidates'][0]['content']['parts'][0]['text']
            st.rerun()
        else: st.error(err)

# --- VISUAL PREVIEW & EXPORT ---
if st.session_state.generated_sow:
    st.divider()
    st.subheader("📄 Visual Preview")
    st.markdown('<div class="sow-preview">', unsafe_allow_html=True)
    
    p_content = st.session_state.generated_sow
    calc_url = CALCULATOR_LINKS.get(sow_key, "https://calculator.aws/")
    p_content = p_content.replace("link", f'[Estimate Link]({calc_url})')
    
    # Handle Architecture Image Injection in Preview
    if "# 4 SOLUTION ARCHITECTURE" in p_content:
        parts = p_content.split("# 4 SOLUTION ARCHITECTURE")
        st.markdown(parts[0] + "# 4 SOLUTION ARCHITECTURE", unsafe_allow_html=True)
        diag_out = SOW_DIAGRAM_MAP.get(sow_key)
        if diag_out and os.path.exists(diag_out):
            st.image(diag_out, caption=f"{sow_key} Architecture Diagram")
        st.markdown(parts[1], unsafe_allow_html=True)
    else:
        st.markdown(p_content, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("💾 Download Microsoft Word (.docx)", use_container_width=True):
        branding = {"sow_name": sow_key, "customer_logo_bytes": customer_logo.getvalue() if customer_logo else None, "doc_date_str": doc_date.strftime("%d %B %Y")}
        docx_data = create_docx_logic(st.session_state.generated_sow, branding, sow_key)
        st.download_button("📥 Click to Download", docx_data, f"SOW_{sow_key.replace(' ', '_')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
