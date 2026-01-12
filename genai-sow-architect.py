import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO

# --- CONFIGURATION ---
st.set_page_config(page_title="GenAI SOW Architect", layout="wide", page_icon="🚀")

# Initialize session state for the generated SOW
if 'generated_sow' not in st.session_state:
    st.session_state.generated_sow = ""

# Function to clear the document
def clear_sow():
    st.session_state.generated_sow = ""

# Function to create Word document
def create_docx(text_content):
    doc = Document()
    doc.add_heading('Scope of Work Document', 0)
    
    # Very simple markdown-to-docx logic: treat # as headers, others as paragraphs
    for line in text_content.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        else:
            doc.add_paragraph(line)
            
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛠️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google AI Studio API Key")
    
    st.divider()
    st.header("📋 Project Details")
    
    # Pre-seeded Dropdown Options
    solution_options = [
        "Multi Agent Store Advisor",
        "Intelligent Search",
        "Recommendation",
        "AI Agents Demand Forecasting",
        "Banner Audit using LLM",
        "Image Enhancement",
        "Virtual Try-On",
        "Agentic AI L1 Support",
        "Product Listing Standardization",
        "AI Agents Based Pricing Module",
        "Cost, Margin Visibility & Insights using LLM",
        "AI Trend Simulator",
        "Virtual Data Analyst (Text to SQL)",
        "Multilingual Call Analysis",
        "Customer Review Analysis",
        "Sales Co-Pilot",
        "Research Co-Pilot",
        "Product Copy Generator",
        "Multi-agent e-KYC & Onboarding",
        "Document / Report Audit",
        "RBI Circular Scraping & Insights Bot",
        "Visual Inspection",
        "AIoT based CCTV Surveillance",
        "Multilingual Voice Bot",
        "SOP Creation",
        "Other (Please specify)"
    ]
    
    solution_type = st.selectbox("Solution Type", solution_options)
    
    # Free text for "Other"
    custom_solution = ""
    if solution_type == "Other (Please specify)":
        custom_solution = st.text_input("Specify Solution Name", placeholder="Enter custom solution name...")
    
    final_solution_name = custom_solution if solution_type == "Other (Please specify)" else solution_type

    engagement_type = st.selectbox("Engagement Type", ["Proof of Concept (PoC)", "MVP", "Production"])
    industry = st.text_input("Industry / Domain", "Retail & Commerce")
    duration = st.text_input("Timeline (Duration)", "4-6 Weeks")
    
    if st.button("Reset Document", on_click=clear_sow, use_container_width=True):
        st.rerun()

# --- MAIN UI ---
st.title("🚀 GenAI SOW Architect Agent")
st.markdown("Automate enterprise-grade Scope of Work documents with professional consulting standards.")

# Visual Separator
st.divider()

# Form Layout for Business Context and Stakeholders
with st.container():
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("🎯 Business Context")
        objective = st.text_area("Business Objective", 
                                "Describe the core challenge and the desired AI-driven resolution...",
                                height=120)
        outcomes = st.multiselect("Key Outcomes Expected", 
            ["Reduced Response Time", "Automated SOP Mapping", "Cost Savings", "User Engagement", "Accuracy Improvement", "Metadata Extraction", "Revenue Growth", "Operational Efficiency"],
            default=["Operational Efficiency", "Accuracy Improvement"])

    with col2:
        st.subheader("👥 Stakeholders")
        st_p1, st_p2 = st.columns(2)
        with st_p1:
            p_name = st.text_input("Partner Lead Name", "Gaurav Kankaria")
            p_title = st.text_input("Partner Lead Title", "Head of Analytics & ML")
        with st_p2:
            c_name = st.text_input("Customer Lead Name", "Cheten Dev")
            c_title = st.text_input("Customer Lead Title", "Head of Product Design")
        
        aws_name = st.text_input("AWS Contact", "Anubhav Sood")

# --- GENERATION LOGIC ---
if st.button("Generate Enterprise SOW", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠️ Please enter an API Key in the sidebar configuration.")
    elif solution_type == "Other (Please specify)" and not custom_solution:
        st.warning("⚠️ Please specify the solution name for the 'Other' category.")
    else:
        with st.spinner(f"Architecting SOW for {final_solution_name}..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
            
            prompt_text = f"""
            Generate a formal enterprise Scope of Work (SOW) for {final_solution_name} in {industry}.
            
            INPUT DETAILS:
            - Engagement: {engagement_type}
            - Objective: {objective}
            - Outcomes: {', '.join(outcomes)}
            - Timeline: {duration}
            - Partner Lead: {p_name} ({p_title})
            - Customer Lead: {c_name} ({c_title})
            - AWS Contact: {aws_name}
            
            STRICT STRUCTURE (MANDATORY):
            1 TABLE OF CONTENTS
            2 PROJECT OVERVIEW
              2.1 OBJECTIVE
              2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S)
              2.3 ASSUMPTIONS & DEPENDENCIES
              2.4 SUCCESS CRITERIA
            3 SCOPE OF WORK – TECHNICAL PROJECT PLAN (Include week-by-week phases)
            4 SOLUTION ARCHITECTURE (AWS native stack: Bedrock, Lambda, S3, OpenSearch, Step Functions)
            5 TIMELINE & PHASING (Weeks 1 to {duration})
            6 RESOURCES & COST ESTIMATES (Logical infra assumptions)
            7 DELIVERABLES & NEXT STEPS

            Use a professional, consulting tone (McKinsey/Big 4 style). Output ONLY Markdown.
            """
            
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "systemInstruction": {"parts": [{"text": "You are an expert enterprise AI Solutions Architect. You create detailed, deterministic, and professionally formatted SOW documents for Fortune 500 clients."}]}
            }
            
            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    st.session_state.generated_sow = response.json()['candidates'][0]['content']['parts'][0]['text']
                    st.success(f"✅ {final_solution_name} SOW Draft Generated!")
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Error during generation: {str(e)}")

# --- EDITABLE OUTPUT AREA ---
if st.session_state.generated_sow:
    st.divider()
    st.subheader("📝 Review & Edit SOW Draft")
    st.info("The draft below is fully editable. Your changes will be reflected in the final Word download.")
    
    # SOW Editor
    edited_sow = st.text_area(
        label="Document Editor",
        value=st.session_state.generated_sow,
        height=650,
        key="sow_editor"
    )
    
    # Sync with session state
    st.session_state.generated_sow = edited_sow
    
    # Actions
    act_col1, act_col2 = st.columns([1, 3])
    with act_col1:
        # Generate Word bytes
        docx_bytes = create_docx(st.session_state.generated_sow)
        
        st.download_button(
            label="📥 Download Word (.docx)",
            data=docx_bytes,
            file_name=f"SOW_{final_solution_name.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with act_col2:
        st.success("✨ Ready for export! Click download to get your Microsoft Word document.")
