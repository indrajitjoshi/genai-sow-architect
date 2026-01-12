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
    .main {
        background-color: #f8fafc;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .stTextArea textarea {
        border-radius: 10px;
    }
    .stTextInput input {
        border-radius: 8px;
    }
    .block-container {
        padding-top: 2rem;
    }
    .sow-preview {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        font-family: 'Inter', sans-serif;
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
    # Add a professional title
    title = doc.add_heading('Scope of Work Document', 0)
    title.alignment = 1 # Center
    
    # Process lines for basic formatting
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

# --- SIDEBAR: SETTINGS & RESET ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.title("SOW Architect")
    st.caption("v2.0 Enterprise Edition")
    
    with st.expander("🔑 API Configuration", expanded=True):
        api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google AI Studio API Key")
        st.caption("Your key is not stored permanently.")
    
    st.divider()
    
    if st.button("🗑️ Reset All Fields", on_click=clear_sow, use_container_width=True):
        st.rerun()
        
    st.info("💡 **Pro Tip**: Use the 'Other' option in Solution Type to define niche agentic workflows.")

# --- MAIN UI ---
st.title("🚀 GenAI Scope of Work Architect")
st.markdown("Bridge the gap between business objectives and technical implementation with AI-generated SOWs.")

# --- STEP 1: PROJECT INTAKE ---
st.header("1. Project Intake")
with st.container():
    col_a, col_b = st.columns([1, 1], gap="medium")
    
    with col_a:
        st.subheader("🛠️ Solution Selection")
        
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
        
        solution_type = st.selectbox("Select Target Solution", solution_options, index=0)
        
        final_solution_name = solution_type
        if solution_type == "Other (Please specify)":
            custom_solution = st.text_input("Specify Custom Solution Name", placeholder="e.g. Legal Contract Review Agent")
            final_solution_name = custom_solution

        engagement_type = st.segmented_control("Engagement Type", ["PoC", "MVP", "Production"], default="PoC")
        
    with col_b:
        st.subheader("🏢 Market Context")
        industry = st.text_input("Industry / Domain", placeholder="e.g. Retail, Healthcare, Fintech")
        duration = st.text_input("Timeline / Duration", placeholder="e.g. 4-6 Weeks")

st.divider()

# --- STEP 2: OBJECTIVES & STAKEHOLDERS ---
st.header("2. Objectives & Stakeholders")
with st.container():
    col_c, col_d = st.columns(2, gap="medium")
    
    with col_c:
        objective = st.text_area(
            "Business Objective", 
            placeholder="What business problem are we solving? (e.g., Automate manual ad compliance checking to reduce turnaround time from 2 days to 2 hours.)",
            height=150
        )
        outcomes = st.multiselect(
            "Expected Success Metrics", 
            ["Reduced Response Time", "Automated SOP Mapping", "Cost Savings", "Improved User UX", "Higher Accuracy", "Metadata Richness", "Revenue Growth", "Security Compliance"],
            default=["Higher Accuracy", "Cost Savings"]
        )

    with col_d:
        st.markdown("**Core Project Team**")
        st_p1, st_p2 = st.columns(2)
        with st_p1:
            p_name = st.text_input("Partner Lead", placeholder="Lead Name")
            p_title = st.text_input("Partner Title", placeholder="e.g. Solution Architect")
        with st_p2:
            c_name = st.text_input("Customer Lead", placeholder="Lead Name")
            c_title = st.text_input("Customer Title", placeholder="e.g. Head of Product")
        
        aws_name = st.text_input("AWS Executive Sponsor", placeholder="AWS Account Team Contact")

# --- GENERATION TRIGGER ---
st.write("")
if st.button("✨ Architect Scope of Work", type="primary", use_container_width=True):
    if not api_key:
        st.warning("⚠️ Please provide a Gemini API Key in the sidebar to proceed.")
    elif solution_type == "Other (Please specify)" and not final_solution_name:
        st.error("⚠️ Please specify the solution name for the 'Other' category.")
    elif not objective:
        st.error("⚠️ Please define the Business Objective.")
    else:
        with st.spinner(f"Generating professional SOW for {final_solution_name}..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
            
            prompt_text = f"""
            Generate a formal enterprise Scope of Work (SOW) for {final_solution_name} in the {industry} industry.
            
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
              2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM (Include a table layout)
              2.3 ASSUMPTIONS & DEPENDENCIES (Data access, AWS environment, etc.)
              2.4 SUCCESS CRITERIA (Tie back to outcomes)
            3 SCOPE OF WORK – TECHNICAL PROJECT PLAN (Detail phases like Requirements, Development, Testing, Demo)
            4 SOLUTION ARCHITECTURE (Describe the AWS native stack: Amazon Bedrock, Lambda, S3, OpenSearch, Step Functions)
            5 TIMELINE & PHASING (Detailed weekly breakdown for {duration})
            6 RESOURCES & COST ESTIMATES (Logical infrastructure cost assumptions)
            7 DELIVERABLES & NEXT STEPS (Documentation, Codebase, PoC Demo)

            Maintain a professional, executive-level consulting tone throughout. Output the response in ONLY Markdown.
            """
            
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "systemInstruction": {"parts": [{"text": "You are a senior GenAI Solutions Architect at a top-tier consulting firm. You specialize in AWS cloud architecture and professional enterprise documentation."}]}
            }
            
            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    st.session_state.generated_sow = response.json()['candidates'][0]['content']['parts'][0]['text']
                    st.balloons()
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Error during document generation: {str(e)}")

# --- STEP 3: EDIT & EXPORT ---
if st.session_state.generated_sow:
    st.divider()
    st.header("3. Review & Refine")
    st.markdown("Adjust the generated content below. Changes are saved automatically for export.")
    
    # Using a tab layout to separate Editor and Preview
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
    
    # Export Actions
    st.write("")
    exp_col1, exp_col2 = st.columns([1, 2])
    with exp_col1:
        docx_data = create_docx(st.session_state.generated_sow)
        st.download_button(
            label="📥 Download Microsoft Word (.docx)",
            data=docx_data,
            file_name=f"SOW_{final_solution_name.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with exp_col2:
        st.success("✨ Document finalized. Your edits will be included in the .docx file.")
