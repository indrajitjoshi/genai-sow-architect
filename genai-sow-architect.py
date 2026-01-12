import streamlit as st
import requests
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="GenAI SOW Architect", layout="wide", page_icon="🚀")

# Initialize session state for the generated SOW
if 'generated_sow' not in st.session_state:
    st.session_state.generated_sow = ""

# Function to clear the document
def clear_sow():
    st.session_state.generated_sow = ""

# --- SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google AI Studio API Key")
    
    st.divider()
    st.header("Project Details")
    solution_type = st.selectbox("Solution Type", [
        "GenAI Chatbot (RAG)", 
        "Image Inspection / Vision AI", 
        "Compliance & Audit Agent",
        "Agentic Workflow Automation",
        "Document Processing Engine"
    ])
    engagement_type = st.selectbox("Engagement Type", ["Proof of Concept (PoC)", "MVP", "Production"])
    industry = st.text_input("Industry / Domain", "Retail & QSR")
    duration = st.text_input("Timeline (Duration)", "4 Weeks")
    
    if st.button("Reset Document", on_click=clear_sow):
        st.rerun()

# --- MAIN UI ---
st.title("🚀 GenAI SOW Architect Agent")
st.markdown("Generate and edit enterprise-grade Scope of Work documents autonomously.")

# Form Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Business Context")
    objective = st.text_area("Business Objective", 
                            "Automate customer support queries and provide personalized resolution using customer data and SOPs.",
                            height=100)
    outcomes = st.multiselect("Key Outcomes Expected", 
        ["Reduced Response Time", "Automated SOP Mapping", "Cost Savings", "User Engagement", "Accuracy Improvement", "Metadata Extraction"],
        default=["Reduced Response Time", "Automated SOP Mapping"])

with col2:
    st.subheader("Stakeholders")
    p_name = st.text_input("Partner Lead Name", "Gaurav Kankaria")
    p_title = st.text_input("Partner Lead Title", "Head of Analytics & ML")
    c_name = st.text_input("Customer Lead Name", "Prabhjot Singh")
    c_title = st.text_input("Customer Lead Title", "Marketing Manager")

# --- GENERATION LOGIC ---
if st.button("Generate SOW Document", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠️ Please enter an API Key in the sidebar.")
    else:
        with st.spinner("Consulting LLM is architecting your SOW..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
            
            # Detailed Prompt to mirror Jubilant/Nykaa PDFs
            prompt_text = f"""
            Generate a formal enterprise Scope of Work (SOW) for {solution_type} in {industry}.
            
            INPUT DETAILS:
            - Objective: {objective}
            - Outcomes: {', '.join(outcomes)}
            - Timeline: {duration}
            - Partner Lead: {p_name} ({p_title})
            - Customer Lead: {c_name} ({c_title})
            
            STRICT STRUCTURE (MANDATORY):
            1 TABLE OF CONTENTS
            2 PROJECT OVERVIEW
              2.1 OBJECTIVE
              2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S)
              2.3 ASSUMPTIONS & DEPENDENCIES
              2.4 SUCCESS CRITERIA
            3 SCOPE OF WORK – TECHNICAL PROJECT PLAN (Include week-by-week estimates)
            4 SOLUTION ARCHITECTURE (Describe AWS native stack: Bedrock, Lambda, S3, OpenSearch)
            5 TIMELINE & PHASING
            6 RESOURCES & COST ESTIMATES
            7 DELIVERABLES & NEXT STEPS

            Use a professional, formal consulting tone. Output ONLY Markdown.
            """
            
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "systemInstruction": {"parts": [{"text": "You are a senior enterprise GenAI Solution Architect. Write precise, professional SOWs for Fortune 500 clients."}]}
            }
            
            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    st.session_state.generated_sow = response.json()['candidates'][0]['content']['parts'][0]['text']
                    st.success("✅ SOW Generated Successfully!")
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- EDITABLE OUTPUT AREA ---
if st.session_state.generated_sow:
    st.divider()
    st.subheader("📝 Review & Edit Draft")
    st.caption("The draft below is fully editable. You can modify sections, fix tables, or add details before downloading.")
    
    # We use a key 'sow_editor' to maintain the widget state across reruns
    edited_sow = st.text_area(
        label="SOW Markdown Editor",
        value=st.session_state.generated_sow,
        height=800,
        key="sow_editor",
        help="Make manual changes here. Changes are saved to memory for download."
    )
    
    # Update state with edits
    st.session_state.generated_sow = edited_sow
    
    # Action buttons for the edited content
    btn_col1, btn_col2 = st.columns([1, 4])
    with btn_col1:
        st.download_button(
            label="📥 Download as Markdown (.md)",
            data=st.session_state.generated_sow,
            file_name=f"SOW_{industry.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with btn_col2:
        st.info("💡 Tip: You can copy this Markdown into Word or a PDF converter for final branding.")
