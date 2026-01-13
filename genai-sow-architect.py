import streamlit as st
import requests
import json
from docx import Document
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
    .block-container { padding-top: 2rem; }
    .sow-preview {
        background-color: white;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for the generated SOW
if 'generated_sow' not in st.session_state:
    st.session_state.generated_sow = ""

# Function to clear the document
def clear_sow():
    st.session_state.generated_sow = ""

# Function to create Word document
def create_docx(text_content):
    doc = Document()
    title = doc.add_heading('Scope of Work Document', 0)
    title.alignment = 1 # Center
    
    for line in text_content.split('\n'):
        line = line.strip()
        if not line:
            doc.add_paragraph("")
            continue
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        else:
            doc.add_paragraph(line)
            
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- SIDEBAR: SETTINGS & PROJECT INTAKE ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("SOW Architect")
    st.caption("Enterprise POC/MVP Edition")
    
    with st.expander("🔑 API Configuration", expanded=True):
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
        final_solution = st.text_input("Specify Solution Name")

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
        final_industry = st.text_input("Specify Industry")

    duration = st.text_input("Timeline / Duration", "4 Weeks")
    
    if st.button("🗑️ Reset All Fields", on_click=clear_sow, use_container_width=True):
        st.rerun()

# --- MAIN UI ---
st.title("🚀 GenAI Scope of Work Architect")
st.markdown("Bridge business objectives and technical implementation with enterprise-standard SOW documentation.")

# --- STEP 2: DETAILS & STAKEHOLDERS ---
st.header("2. Objectives & Stakeholders")
col_c, col_d = st.columns(2, gap="medium")

with col_c:
    objective = st.text_area(
        "Business Objective", 
        placeholder="e.g., Validate the feasibility of an AI powered Ads Banner Compliance tool to reduce manual review effort.",
        height=150
    )
    outcomes = st.multiselect(
        "Expected Success Metrics", 
        ["Reduced Response Time", "Automated SOP Mapping", "Cost Savings", "Higher Accuracy", "Metadata Richness", "Revenue Growth", "Security Compliance"],
        default=["Higher Accuracy", "Cost Savings"]
    )

with col_d:
    st.markdown("**Project Team**")
    st_p1, st_p2 = st.columns(2)
    with st_p1:
        p_name = st.text_input("Partner Lead", "Gaurav Kankaria")
        p_title = st.text_input("Partner Title", "Head of Analytics & ML")
    with st_p2:
        c_name = st.text_input("Customer Lead", "Cheten Dev")
        c_title = st.text_input("Customer Title", "Head of Product Design")
    
    aws_name = st.text_input("AWS Executive Sponsor", "Anubhav Sood")

# --- GENERATION TRIGGER ---
if st.button("✨ Architect Scope of Work", type="primary", use_container_width=True):
    if not api_key:
        st.warning("⚠️ Please provide a Gemini API Key in the sidebar.")
    elif not objective:
        st.error("⚠️ Please define the Business Objective.")
    else:
        with st.spinner(f"Architecting SOW for {final_solution}..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
            
            # This prompt is engineered to mirror the structure of Nykaa/Jubilant SOWs
            prompt_text = f"""
            Generate a formal enterprise Scope of Work (SOW) for {final_solution} in {final_industry}.
            
            INPUT DETAILS:
            - Engagement Type: {engagement_type}
            - Primary Objective: {objective}
            - Success Metrics: {', '.join(outcomes)}
            - Timeline: {duration}
            - Partner Team: {p_name} ({p_title})
            - Customer Team: {c_name} ({c_title})
            - AWS Sponsor: {aws_name}
            
            STRICT STRUCTURE (MANDATORY):
            1 TABLE OF CONTENTS
            2 PROJECT OVERVIEW
              2.1 OBJECTIVE
              2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM (Include table with Name, Title, Email/Contact Info)
              2.3 ASSUMPTIONS & DEPENDENCIES (Separate Dependencies and Assumptions)
              2.4 PROJECT SUCCESS CRITERIA (Numbered list)
            3 SCOPE OF WORK – TECHNICAL PROJECT PLAN (Include Infrastructure Setup, Core Workflows, and Backend Components)
            4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM (Describe AWS-native services like Bedrock, S3, Lambda, OpenSearch)
            5 RESOURCES & COST ESTIMATES (Include POC Development cost model and AWS Infrastructure cost assumptions)

            Maintain the professional, executive-level consulting tone found in Oneture/AWS partner SOWs. 
            Output the response in ONLY Markdown.
            """
            
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "systemInstruction": {"parts": [{"text": "You are a senior Solutions Architect at Oneture. You generate detailed SOWs that follow the specific formatting of provided Nykaa and Jubilant PDF examples."}]}
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
    st.header("3. Review & Refine")
    
    tab_edit, tab_preview = st.tabs(["✍️ Document Editor", "📄 Visual Preview"])
    
    with tab_edit:
        edited_sow = st.text_area(
            label="Markdown Editor",
            value=st.session_state.generated_sow,
            height=600,
            key="sow_editor",
            label_visibility="collapsed"
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
        st.success("✨ SOW document is ready. Changes made in the editor will be reflected in the Word download.")
