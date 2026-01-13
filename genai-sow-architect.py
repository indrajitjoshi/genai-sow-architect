import streamlit as st
from datetime import date
import io
import re

# --- CONFIGURATION ---
st.set_page_config(
    page_title="GenAI SOW Architect", 
    layout="wide", 
    page_icon="📄",
    initial_sidebar_state="expanded"
)

# Custom CSS for an Enterprise UI
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .stTextArea textarea { border-radius: 10px; }
    .stTextInput input { border-radius: 8px; }
    .block-container { padding-top: 1.5rem; }
    .sow-preview {
        background-color: white;
        padding: 40px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.7;
        color: #1e293b;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    h1, h2, h3 { color: #0f172a; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: 600; }
    [data-testid="stExpander"] { border: none; box-shadow: none; background: transparent; }
    .stakeholder-header { 
        background-color: #f1f5f9; 
        padding: 8px 12px; 
        border-radius: 6px; 
        margin-bottom: 10px; 
        font-weight: bold;
        color: #334155;
        border-left: 4px solid #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CACHED UTILITIES ---
def create_docx_logic(text_content, branding_info):
    """
    Generates the Word document with strict page isolation and markdown cleanup.
    Page 1: Cover
    Page 2: Table of Contents (Isolated)
    Page 3: Project Overview (2.1 -> 2.2 -> 2.3 sequence)
    """
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    
    # --- PAGE 1: COVER PAGE ---
    if branding_info.get('aws_pn_logo_bytes'):
        p_top = doc.add_paragraph()
        p_top.alignment = WD_ALIGN_PARAGRAPH.LEFT
        try:
            run = p_top.add_run()
            run.add_picture(io.BytesIO(branding_info['aws_pn_logo_bytes']), width=Inches(1.0))
        except:
            p_top.add_run("aws partner network").bold = True

    doc.add_paragraph("\n" * 3)
    
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(branding_info['solution_name'])
    run.font.size = Pt(26)
    run.font.bold = True
    
    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle_p.add_run("Scope of Work Document")
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
    
    doc.add_paragraph("\n" * 4)
    
    logo_table = doc.add_table(rows=1, cols=3)
    logo_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    def insert_logo_to_cell(cell, bytes_data, width_val, fallback_text):
        cell.paragraphs[0].text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if bytes_data:
            try:
                p.add_run().add_picture(io.BytesIO(bytes_data), width=Inches(width_val))
            except:
                p.add_run(fallback_text).bold = True
        else:
            p.add_run(fallback_text).bold = True

    insert_logo_to_cell(logo_table.rows[0].cells[0], branding_info.get('customer_logo_bytes'), 1.4, "[Customer Logo]")
    insert_logo_to_cell(logo_table.rows[0].cells[1], branding_info.get('oneture_logo_bytes'), 2.2, "ONETURE")
    insert_logo_to_cell(logo_table.rows[0].cells[2], branding_info.get('aws_adv_logo_bytes'), 1.3, "AWS Advanced")

    doc.add_paragraph("\n" * 4)
    
    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_p.add_run(branding_info['doc_date_str'])
    run.font.size = Pt(12)
    run.font.bold = True
    
    # End Page 1
    doc.add_page_break()
    
    # --- CONTENT PROCESSING ---
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    lines = text_content.split('\n')
    i = 0
    in_toc_section = False
    toc_already_added = False
    overview_started = False

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            # Add small spacing to keep document flow
            if i > 0 and lines[i-1].strip():
                doc.add_paragraph("")
            i += 1
            continue

        # Prepare strings for structure detection - Use regex for cleaner stripping
        # Remove markdown bolding and italics artifacts
        line_clean = re.sub(r'\*+', '', line).strip()
        # Extract title text without header markers
        clean_text = re.sub(r'^#+\s*', '', line_clean).strip()
        upper_text = clean_text.upper()

        # 1. Page Break Trigger: Section 2 MUST start on Page 3
        # Detection matches any line starting with 2 and PROJECT OVERVIEW, or a header with it
        if ("2 PROJECT OVERVIEW" in upper_text) and (line.startswith('#') or line.startswith('2')) and not overview_started:
            doc.add_page_break()
            in_toc_section = False
            overview_started = True
            doc.add_heading(clean_text, level=1)
            i += 1
            continue

        # 2. Section 1 Trigger: TOC MUST stay on Page 2
        if "1 TABLE OF CONTENTS" in upper_text:
            if not toc_already_added:
                in_toc_section = True
                toc_already_added = True
                doc.add_heading("1 TABLE OF CONTENTS", level=1)
            i += 1
            continue

        # Markdown Table Detection
        if line.startswith('|') and i + 1 < len(lines) and lines[i+1].strip().startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 3:
                data_lines = [l for l in table_lines if not set(l).issubset({'|', '-', ' ', ':'})]
                if len(data_lines) >= 2:
                    headers = [c.strip() for c in data_lines[0].split('|') if c.strip()]
                    table = doc.add_table(rows=1, cols=len(headers))
                    table.style = 'Table Grid'
                    hdr_cells = table.rows[0].cells
                    for idx, h in enumerate(headers):
                        hdr_cells[idx].text = h
                    for row_str in data_lines[1:]:
                        row_cells = table.add_row().cells
                        r_data = [c.strip() for c in row_str.split('|') if c.strip()]
                        for idx, c_text in enumerate(r_data):
                            if idx < len(row_cells):
                                row_cells[idx].text = c_text
                doc.add_paragraph("")
            continue

        # Standard Elements Parsing
        if line.startswith('# '):
            doc.add_heading(clean_text, level=1)
        elif line.startswith('## '):
            p = doc.add_heading(clean_text, level=2)
            if in_toc_section:
                p.paragraph_format.left_indent = Inches(0.4)
        elif line.startswith('### '):
            p = doc.add_heading(clean_text, level=3)
            if in_toc_section:
                p.paragraph_format.left_indent = Inches(0.8)
        elif line.startswith('- ') or line.startswith('* '):
            # Strip the bullet marker for standard list rendering
            bullet_text = re.sub(r'^[-*]\s*', '', clean_text)
            p = doc.add_paragraph(bullet_text, style='List Bullet')
            if in_toc_section:
                p.paragraph_format.left_indent = Inches(0.4)
        else:
            # Handle plain body text or TOC sub-items
            p = doc.add_paragraph(clean_text)
            if in_toc_section and len(clean_text) > 3 and clean_text[0].isdigit():
                 p.paragraph_format.left_indent = Inches(0.4)
            
            # Segregation bolding logic for key category labels in Project Overview
            if any(key in upper_text for key in ["DEPENDENCIES:", "ASSUMPTIONS:", "SPONSOR:", "CONTACTS:"]):
                if p.runs:
                    p.runs[0].bold = True
        i += 1
            
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- INITIALIZATION ---
if 'generated_sow' not in st.session_state:
    st.session_state.generated_sow = ""

if 'stakeholders' not in st.session_state:
    import pandas as pd
    st.session_state.stakeholders = {
        "Partner": pd.DataFrame([{"Name": "Gaurav Kankaria", "Title": "Head of Analytics & ML", "Email": "gaurav.kankaria@oneture.com"}]),
        "Customer": pd.DataFrame([{"Name": "Cheten Dev", "Title": "Head of Product Design", "Email": "cheten.dev@nykaa.com"}]),
        "AWS": pd.DataFrame([{"Name": "Anubhav Sood", "Title": "AWS Account Executive", "Email": "anbhsood@amazon.com"}]),
        "Escalation": pd.DataFrame([
            {"Name": "Omkar Dhavalikar", "Title": "AI/ML Lead", "Email": "omkar.dhavalikar@oneture.com"},
            {"Name": "Gaurav Kankaria", "Title": "Head of Analytics and AIML", "Email": "gaurav.kankaria@oneture.com"}
        ])
    }

def clear_sow():
    st.session_state.generated_sow = ""

# --- SIDEBAR: PROJECT INTAKE ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("SOW Architect")
    st.caption("Enterprise POC/MVP Engine")
    
    with st.expander("🔑 API Key", expanded=False):
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    st.header("📋 1. Project Intake")

    solution_options = [
        "Multi Agent Store Advisor", "Intelligent Search", "Recommendation", 
        "AI Agents Demand Forecasting", "Banner Audit using LLM", "Image Enhancement", 
        "Virtual Try-On", "Agentic AI L1 Support", "Product Listing Standardization", 
        "AI Agents Based Pricing Module", "Cost, Margin Visibility & Insights using LLM", 
        "AI Trend Simulator", "Virtual Data Analyst (Text to SQL)", "Multilingual Call Analysis", 
        "Customer Review Analysis", "Sales Co-Pilot", "Research Co-Pilot", 
        "Product Copy Generator", "Multi-agent e-KYC & Onboarding", "Document / Report Audit", 
        "RBI Circular Scraping & Insights Bot", "Visual Inspection", 
        "AIoT based CCTV Surveillance", "Multilingual Voice Bot", "SOP Creation", "Other (Please specify)"
    ]
    solution_type = st.selectbox("1.1 Solution Type", solution_options)
    final_solution = st.text_input("Specify Solution Name", placeholder="Enter solution...") if solution_type == "Other (Please specify)" else solution_type

    engagement_options = ["Proof of Concept (PoC)", "Pilot", "MVP", "Production Rollout", "Assessment / Discovery", "Support"]
    engagement_type = st.selectbox("1.2 Engagement Type", engagement_options)

    industry_options = ["Retail / E-commerce", "BFSI", "Manufacturing", "Telecom", "Healthcare", "Energy / Utilities", "Logistics", "Media", "Government", "Other (specify)"]
    industry_type = st.selectbox("1.3 Industry / Domain", industry_options)
    final_industry = st.text_input("Specify Industry", placeholder="Enter industry...") if industry_type == "Other (specify)" else industry_type

    duration = st.text_input("Timeline / Duration", "4 Weeks")
    
    if st.button("🗑️ Reset All Fields", on_click=clear_sow, use_container_width=True):
        st.rerun()

# --- MAIN UI ---
st.title("🚀 GenAI Scope of Work Architect")

# --- STEP 0: COVER PAGE BRANDING ---
st.header("📸 Cover Page Branding")
brand_col1, brand_col2 = st.columns(2)
with brand_col1:
    aws_pn_logo = st.file_uploader("Top Left: AWS Partner Network Logo", type=['png', 'jpg', 'jpeg'], key="aws_pn")
    customer_logo = st.file_uploader("Slot 1: Customer Logo", type=['png', 'jpg', 'jpeg'], key="cust_logo")

with brand_col2:
    oneture_logo = st.file_uploader("Slot 2: Oneture Logo", type=['png', 'jpg', 'jpeg'], key="one_logo")
    aws_adv_logo = st.file_uploader("Slot 3: AWS Advanced Logo", type=['png', 'jpg', 'jpeg'], key="aws_adv")
    doc_date = st.date_input("Document Date", date.today())

st.divider()

# --- STEP 2: OBJECTIVES & STAKEHOLDERS ---
st.header("2. Objectives & Stakeholders")

st.subheader("🎯 2.1 Objective")
objective = st.text_area(
    "Define the core business objective:", 
    placeholder="e.g., Development of a Gen AI based WIMO Bot to demonstrate feasibility...",
    height=120
)
outcomes = st.multiselect(
    "Select success metrics:", 
    ["Reduced Response Time", "Automated SOP Mapping", "Cost Savings", "Higher Accuracy", "Metadata Richness", "Revenue Growth", "Security Compliance", "Scalability", "Integration Feasibility"],
    default=["Higher Accuracy", "Cost Savings"]
)

st.divider()

st.subheader("👥 2.2 Project Sponsor(s) / Stakeholder(s) / Project Team")
col_team1, col_team2 = st.columns(2)

with col_team1:
    st.markdown('<div class="stakeholder-header">Partner Executive Sponsor</div>', unsafe_allow_html=True)
    st.session_state.stakeholders["Partner"] = st.data_editor(st.session_state.stakeholders["Partner"], num_rows="dynamic", use_container_width=True, key="ed_partner")

    st.markdown('<div class="stakeholder-header">AWS Executive Sponsor</div>', unsafe_allow_html=True)
    st.session_state.stakeholders["AWS"] = st.data_editor(st.session_state.stakeholders["AWS"], num_rows="dynamic", use_container_width=True, key="ed_aws")

with col_team2:
    st.markdown('<div class="stakeholder-header">Customer Executive Sponsor</div>', unsafe_allow_html=True)
    st.session_state.stakeholders["Customer"] = st.data_editor(st.session_state.stakeholders["Customer"], num_rows="dynamic", use_container_width=True, key="ed_customer")

    st.markdown('<div class="stakeholder-header">Project Escalation Contacts</div>', unsafe_allow_html=True)
    st.session_state.stakeholders["Escalation"] = st.data_editor(st.session_state.stakeholders["Escalation"], num_rows="dynamic", use_container_width=True, key="ed_escalation")

# --- GENERATION ---
if st.button("✨ Generate SOW Document", type="primary", use_container_width=True):
    if not api_key:
        st.warning("⚠️ Enter a Gemini API Key in the sidebar.")
    elif not objective:
        st.error("⚠️ Business Objective is required.")
    else:
        import requests
        with st.spinner(f"Architecting SOW for {final_solution}..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
            
            def get_md(df):
                return df.to_markdown(index=False)

            prompt_text = f"""
            Generate a COMPLETE formal enterprise Scope of Work (SOW) for {final_solution} in {final_industry}.
            
            MANDATORY STRUCTURE:
            1 TABLE OF CONTENTS (Indented sub-items)
            2 PROJECT OVERVIEW
              2.1 OBJECTIVE
              2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM
              2.3 ASSUMPTIONS & DEPENDENCIES
              2.4 PROJECT SUCCESS CRITERIA
            3 SCOPE OF WORK – TECHNICAL PROJECT PLAN
            4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM
            5 RESOURCES & COST ESTIMATES

            CONTENT RULES:
            - NO filler text or introductory sentences between headers 2, 2.1, 2.2, and 2.3.
            - Section 2 must start fresh and immediately with 2.1 Objective.
            - Section 2.2 must keep all stakeholder sections distinct with provided tables.
            - Section 2.3 must clearly segregate into "Dependencies:" and "Assumptions:" labels with bulleted lists.
            - Remove ALL unnecessary asterisks (*) or markdown bolding marks (**) inside text or headings. 
            - Use plain text output only for document content. No markdown symbols like bolding or italics in the body.

            INPUT DETAILS:
            - Engagement Type: {engagement_type}
            - Primary Objective: {objective}
            - Success Metrics: {', '.join(outcomes)}
            - Timeline: {duration}
            
            STAKEHOLDER TABLES:
            {get_md(st.session_state.stakeholders["Partner"])}
            {get_md(st.session_state.stakeholders["Customer"])}
            {get_md(st.session_state.stakeholders["AWS"])}
            {get_md(st.session_state.stakeholders["Escalation"])}

            Tone: Professional consulting. Output: Markdown only.
            """
            
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "systemInstruction": {"parts": [{"text": "You are a senior Solutions Architect. You generate detailed SOW documents. Strictly follow numbering. NO filler text. NO markdown bolding marks or asterisks in the output text. Plain text output only."}]}
            }
            
            try:
                res = requests.post(url, json=payload)
                if res.status_code == 200:
                    st.session_state.generated_sow = res.json()['candidates'][0]['content']['parts'][0]['text']
                    st.balloons()
                else:
                    st.error(f"API Error: {res.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- STEP 3: REVIEW & EXPORT ---
if st.session_state.generated_sow:
    st.divider()
    st.header("3. Review & Export")
    tab_edit, tab_preview = st.tabs(["✍️ Document Editor", "📄 Visual Preview"])
    
    with tab_edit:
        st.session_state.generated_sow = st.text_area(
            label="Modify generated content:", 
            value=st.session_state.generated_sow, 
            height=700, 
            key="sow_editor"
        )
    
    with tab_preview:
        st.markdown(f'<div class="sow-preview">', unsafe_allow_html=True)
        st.markdown(st.session_state.generated_sow)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    
    if st.button("💾 Prepare Microsoft Word Document"):
        branding_info = {
            'solution_name': final_solution,
            'aws_pn_logo_bytes': aws_pn_logo.getvalue() if aws_pn_logo else None,
            'customer_logo_bytes': customer_logo.getvalue() if customer_logo else None,
            'oneture_logo_bytes': oneture_logo.getvalue() if oneture_logo else None,
            'aws_adv_logo_bytes': aws_adv_logo.getvalue() if aws_adv_logo else None,
            'doc_date_str': doc_date.strftime("%d %B %Y")
        }
        
        docx_data = create_docx_logic(st.session_state.generated_sow, branding_info)
        
        st.download_button(
            label="📥 Download Now (.docx)", 
            data=docx_data, 
            file_name=f"SOW_{final_solution.replace(' ', '_')}.docx", 
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
            use_container_width=True
        )
