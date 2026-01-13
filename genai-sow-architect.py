import streamlit as st
import requests
import json
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
from datetime import date

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

# Initialize session states
if 'generated_sow' not in st.session_state:
    st.session_state.generated_sow = ""

if 'stakeholders' not in st.session_state:
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

def create_docx(text_content, branding_data):
    doc = Document()
    
    # --- PAGE 1: COVER PAGE (STRICT PDF LAYOUT) ---
    
    # 1. AWS Partner Network Logo (TOP LEFT)
    if branding_data['aws_pn_logo']:
        try:
            p = doc.add_paragraph()
            run = p.add_run()
            run.add_picture(branding_data['aws_pn_logo'], width=Inches(1.2))
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        except:
            doc.add_paragraph("AWS Partner Network").alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        # Placeholder space if no logo
        doc.add_paragraph("\n")
    
    doc.add_paragraph("\n" * 5) # Gap before title
    
    # 2. Title & Subtitle (CENTER)
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(branding_data['solution_name'])
    run.font.size = Pt(24)
    run.font.bold = True
    
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Scope of Work Document")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B) # Slate grey
    
    doc.add_paragraph("\n" * 2) # Gap before customer logo
    
    # 3. Customer Logo (CENTER)
    if branding_data['customer_logo']:
        try:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(branding_data['customer_logo'], width=Inches(2.5))
        except:
            p = doc.add_paragraph("[Customer Logo Placeholder]")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph("\n" * 6) # Large gap to bottom branding
    
    # 4. Oneture & AWS Advanced Tier (BOTTOM CENTER)
    # Using a table to keep them side-by-side at the bottom
    brand_table = doc.add_table(rows=1, cols=2)
    brand_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Oneture Logo (Left cell, right aligned)
    cell_left = brand_table.rows[0].cells[0]
    p_left = cell_left.paragraphs[0]
    p_left.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if branding_data['oneture_logo']:
        try:
            run = p_left.add_run()
            run.add_picture(branding_data['oneture_logo'], width=Inches(1.3))
        except:
            p_left.add_run("ONETURE")
    
    # AWS Advanced Logo (Right cell, left aligned)
    cell_right = brand_table.rows[0].cells[1]
    p_right = cell_right.paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if branding_data['aws_adv_logo']:
        try:
            run = p_right.add_run()
            run.add_picture(branding_data['aws_adv_logo'], width=Inches(1.3))
        except:
            p_right.add_run("AWS Advanced Tier")

    # 5. Date (BOTTOM CENTER)
    doc.add_paragraph("\n")
    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_p.add_run(branding_data['doc_date'].strftime("%d %B %Y"))
    run.font.size = Pt(12)
    run.font.bold = True
    
    doc.add_page_break()
    
    # --- PAGE 2 ONWARDS: CONTENT ---
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    lines = text_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Table detection
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
            continue

        if not line:
            doc.add_paragraph("")
        elif line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        else:
            doc.add_paragraph(line)
        i += 1
            
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

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

    duration = st.text_input("Timeline / Duration", "4-6 Weeks")
    
    if st.button("🗑️ Reset All Fields", on_click=clear_sow, use_container_width=True):
        st.rerun()

# --- MAIN UI ---
st.title("🚀 GenAI Scope of Work Architect")

# --- STEP 0: COVER PAGE BRANDING ---
st.header("📸 Cover Page Branding")
st.info("Upload the logos to recreate the Cover Page exactly as per the reference document.")

brand_col1, brand_col2 = st.columns(2)
with brand_col1:
    aws_pn_logo = st.file_uploader("Top Left: AWS Partner Network Logo", type=['png', 'jpg', 'jpeg'])
    customer_logo = st.file_uploader("Center: Customer Logo (e.g. Jubilant)", type=['png', 'jpg', 'jpeg'])

with brand_col2:
    oneture_logo = st.file_uploader("Bottom Left: Oneture Logo", type=['png', 'jpg', 'jpeg'])
    aws_adv_logo = st.file_uploader("Bottom Right: AWS Advanced Tier Logo", type=['png', 'jpg', 'jpeg'])

doc_date = st.date_input("Document Date", date.today())

st.divider()

# --- STEP 2: OBJECTIVES & STAKEHOLDERS ---
st.header("2. Objectives & Stakeholders")

# 2.1 OBJECTIVE
st.subheader("🎯 2.1 Objective")
objective = st.text_area(
    "Define the core business objective and problem statement:", 
    placeholder="e.g., Development of a Gen AI based WIMO Bot to demonstrate feasibility...",
    height=120
)
outcomes = st.multiselect(
    "Select success metrics:", 
    ["Reduced Response Time", "Automated SOP Mapping", "Cost Savings", "Higher Accuracy", "Metadata Richness", "Revenue Growth", "Security Compliance", "Scalability", "Integration Feasibility"],
    default=["Higher Accuracy", "Cost Savings"]
)

st.divider()

# 2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S)
st.subheader("👥 2.2 Project Sponsor(s) / Stakeholder(s) / Project Team")
col_team1, col_team2 = st.columns(2)

with col_team1:
    st.markdown('<div class="stakeholder-header">Partner Executive Sponsor (Oneture)</div>', unsafe_allow_html=True)
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
        with st.spinner(f"Architecting SOW for {final_solution}..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
            
            def get_md(df):
                return df.to_markdown(index=False)

            prompt_text = f"""
            Generate a formal enterprise Scope of Work (SOW) for {final_solution} in {final_industry}.
            
            INPUT DETAILS:
            - Engagement Type: {engagement_type}
            - Primary Objective: {objective}
            - Success Metrics: {', '.join(outcomes)}
            - Timeline: {duration}
            
            STAKEHOLDER TABLES:
            ### Partner Executive Sponsor:
            {get_md(st.session_state.stakeholders["Partner"])}
            ### Customer Executive Sponsor:
            {get_md(st.session_state.stakeholders["Customer"])}
            ### AWS Executive Sponsor:
            {get_md(st.session_state.stakeholders["AWS"])}
            ### Project Escalation Contacts:
            {get_md(st.session_state.stakeholders["Escalation"])}
            
            STRICT STRUCTURE:
            1 TABLE OF CONTENTS
            2 PROJECT OVERVIEW
              2.1 OBJECTIVE
              2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM
              2.3 ASSUMPTIONS & DEPENDENCIES
              2.4 PROJECT SUCCESS CRITERIA
            3 SCOPE OF WORK – TECHNICAL PROJECT PLAN
            4 SOLUTION ARCHITECTURE
            5 RESOURCES & COST ESTIMATES

            Tone: Professional consulting. Output: Markdown only.
            """
            
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "systemInstruction": {"parts": [{"text": "You are a senior Solutions Architect at Oneture."}]}
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
        st.session_state.generated_sow = st.text_area(label="Modify generated content:", value=st.session_state.generated_sow, height=700, key="sow_editor")
    with tab_preview:
        st.markdown(f'<div class="sow-preview">', unsafe_allow_html=True)
        st.markdown(st.session_state.generated_sow)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    
    branding_data = {
        'solution_name': final_solution,
        'aws_pn_logo': aws_pn_logo,
        'customer_logo': customer_logo,
        'oneture_logo': oneture_logo,
        'aws_adv_logo': aws_adv_logo,
        'doc_date': doc_date
    }
    
    docx_data = create_docx(st.session_state.generated_sow, branding_data)
    st.download_button(label="📥 Download Microsoft Word (.docx)", data=docx_data, file_name=f"SOW_{final_solution.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
