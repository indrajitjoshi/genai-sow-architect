import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO

# --- CONFIGURATION ---
st.set_page_config(
    page_title="GenAI SOW Architect", 
    layout="wide", 
    page_icon="📄",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner, "Enterprise" look
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
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for the generated SOW
if 'generated_sow' not in st.session_state:
    st.session_state.generated_sow = ""

# Function to clear the document
def clear_sow():
    st.session_state.generated_sow = ""

# Function to create Word document with Table support
def create_docx(text_content):
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    title = doc.add_heading('Scope of Work Document', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    lines = text_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Table detection
        if line.startswith('|') and i + 1 < len(lines) and lines[i+1].strip().startswith('|---'):
            # Find the end of the table
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            
            if len(table_lines) > 2:
                # Extract headers and data
                headers = [c.strip() for c in table_lines[0].split('|') if c.strip()]
                rows = []
                for r in table_lines[2:]:
                    rows.append([c.strip() for c in r.split('|') if c.strip()])
                
                # Add table to doc
                table = doc.add_table(rows=1, cols=len(headers))
                table.style = 'Table Grid'
                hdr_cells = table.rows[0].cells
                for idx, h in enumerate(headers):
                    hdr_cells[idx].text = h
                
                for r_data in rows:
                    row_cells = table.add_row().cells
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
    st.caption("Enterprise POC/MVP Edition")
    
    with st.expander("🔑 API Configuration", expanded=False):
        api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google AI Studio API Key")
    
    st.divider()
    st.header("📋 1. Project Intake")

    # 1.1 Solution Type
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
    
    final_solution = solution_type
    if solution_type == "Other (Please specify)":
        final_solution = st.text_input("Specify Solution Name", placeholder="Enter specific solution...")

    # 1.2 Engagement Type
    engagement_options = [
        "Proof of Concept (PoC)", "Pilot", "MVP", 
        "Production Rollout", "Assessment / Discovery", "Support"
    ]
    engagement_type = st.selectbox("1.2 Engagement Type", engagement_options)

    # 1.3 Industry / Domain
    industry_options = [
        "Retail / E-commerce", "BFSI", "Manufacturing", "Telecom", 
        "Healthcare", "Energy / Utilities", "Logistics", "Media", 
        "Government", "Other (specify)"
    ]
    industry_type = st.selectbox("1.3 Industry / Domain", industry_options)
    
    final_industry = industry_type
    if industry_type == "Other (specify)":
        final_industry = st.text_input("Specify Industry", placeholder="Enter specific domain...")

    duration = st.text_input("Timeline / Duration", "4 Weeks")
    
    if st.button("🗑️ Reset All Fields", on_click=clear_sow, use_container_width=True):
        st.rerun()

# --- MAIN UI ---
st.title("🚀 GenAI Scope of Work Architect")
st.markdown("Generate professional enterprise-standard SOW documents using AWS GenAI best practices.")

# --- STEP 2: DETAILS & STAKEHOLDERS ---
st.header("2. Objectives & Stakeholders")

# Objective Section
st.subheader("🎯 Business Context")
objective = st.text_area(
    "Define the core business objective and problem statement:", 
    placeholder="e.g., Validate the feasibility of an AI powered Ads Banner Compliance tool to reduce manual review effort and improve accuracy.",
    height=120
)

outcomes = st.multiselect(
    "Select expected success metrics:", 
    ["Reduced Response Time", "Automated SOP Mapping", "Cost Savings", "Higher Accuracy", "Metadata Richness", "Revenue Growth", "Security Compliance", "Scalability", "Integration Feasibility"],
    default=["Higher Accuracy", "Cost Savings"]
)

st.divider()

# Stakeholder Grid - Rectifying clutter by using a cleaner grouping
st.subheader("👥 Project Stakeholders")
p_col, c_col, a_col = st.columns(3, gap="large")

with p_col:
    st.info("**Partner Team (Oneture)**")
    p_name = st.text_input("Partner Lead Name", "Gaurav Kankaria")
    p_title = st.text_input("Partner Lead Title", "Head of Analytics & ML")

with c_col:
    st.info("**Customer Team**")
    c_name = st.text_input("Customer Lead Name", "Cheten Dev")
    c_title = st.text_input("Customer Lead Title", "Head of Product Design")

with a_col:
    st.info("**AWS Team**")
    aws_name = st.text_input("AWS Executive Sponsor", "Anubhav Sood")
    aws_title = st.text_input("AWS Role", "AWS Account Executive")

# --- GENERATION TRIGGER ---
st.write("")
if st.button("✨ Generate Professional SOW Document", type="primary", use_container_width=True):
    if not api_key:
        st.warning("⚠️ Please provide a Gemini API Key in the sidebar.")
    elif not objective:
        st.error("⚠️ Please define the Business Objective.")
    else:
        with st.spinner(f"Architecting SOW for {final_solution}..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
            
            prompt_text = f"""
            Generate a formal enterprise Scope of Work (SOW) for {final_solution} in {final_industry}.
            
            INPUT DETAILS:
            - Engagement: {engagement_type}
            - Objective: {objective}
            - Outcomes: {', '.join(outcomes)}
            - Timeline: {duration}
            - Partner Team: {p_name} ({p_title})
            - Customer Team: {c_name} ({c_title})
            - AWS Team: {aws_name} ({aws_title})
            
            STRICT STRUCTURE (MANDATORY):
            1 TABLE OF CONTENTS
            2 PROJECT OVERVIEW
              2.1 OBJECTIVE
              2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM (Include a clean Markdown table with Name, Title, and Email/Contact)
              2.3 ASSUMPTIONS & DEPENDENCIES (Separate lists for Dependencies and Assumptions)
              2.4 PROJECT SUCCESS CRITERIA (Numbered list mapped to outcomes)
            3 SCOPE OF WORK – TECHNICAL PROJECT PLAN (Detail phases like Infrastructure Setup, Core Workflows, and Backend Components)
            4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM (Describe AWS-native stack: Bedrock, S3, Lambda, OpenSearch, etc.)
            5 RESOURCES & COST ESTIMATES (Include POC cost model and AWS infra assumptions)

            Use a professional, consulting tone. Output ONLY Markdown.
            """
            
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "systemInstruction": {"parts": [{"text": "You are a senior Solutions Architect at Oneture. You generate detailed SOWs that mirror the professional formatting and clarity of the Nykaa and Jubilant PDF examples provided."}]}
            }
            
            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    st.session_state.generated_sow = response.json()['candidates'][0]['content']['parts'][0]['text']
                    st.balloons()
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- STEP 3: EDIT & EXPORT ---
if st.session_state.generated_sow:
    st.divider()
    st.header("3. Review & Export")
    
    tab_edit, tab_preview = st.tabs(["✍️ Document Editor", "📄 Visual Preview"])
    
    with tab_edit:
        edited_sow = st.text_area(
            label="Edit the content below before downloading:",
            value=st.session_state.generated_sow,
            height=700,
            key="sow_editor"
        )
        st.session_state.generated_sow = edited_sow
    
    with tab_preview:
        st.markdown(f'<div class="sow-preview">', unsafe_allow_html=True)
        st.markdown(st.session_state.generated_sow)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    exp_col1, exp_col2 = st.columns([1, 2])
    with exp_col1:
        docx_data = create_docx(st.session_state.generated_sow)
        st.download_button(
            label="📥 Download Microsoft Word (.docx)",
            data=docx_data,
            file_name=f"SOW_{final_solution.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with exp_col2:
        st.success("✨ SOW document generated. Tables have been formatted for Word compatibility.")
