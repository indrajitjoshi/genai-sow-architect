import streamlit as st
import requests
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="GenAI SOW Architect", layout="wide")

# Get API Key from Streamlit Secrets or manual input
api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.title("🚀 GenAI SOW Architect Agent")
st.markdown("Generate enterprise-grade Scope of Work documents autonomously.")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("Project Basics")
    solution_type = st.selectbox("Solution Type", [
        "GenAI Chatbot (RAG)", 
        "Image Inspection / Vision AI", 
        "Compliance & Audit Agent",
        "Agentic Workflow Automation"
    ])
    engagement_type = st.selectbox("Engagement Type", ["PoC", "MVP", "Production"])
    industry = st.text_input("Industry", "Retail / QSR")
    duration = st.text_input("Duration", "4 Weeks")

# --- MAIN FORM ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Business Context")
    objective = st.text_area("Business Objective", "Automate customer support queries...")
    outcomes = st.multiselect("Expected Outcomes", 
        ["Reduced Response Time", "Automated SOP Mapping", "Cost Savings", "User Engagement"],
        default=["Reduced Response Time"])

with col2:
    st.subheader("Stakeholders")
    p_name = st.text_input("Partner Lead", "Gaurav Kankaria")
    c_name = st.text_input("Customer Lead", "Prabhjot Singh")

# --- GENERATION LOGIC ---
if st.button("Generate SOW Document"):
    if not api_key:
        st.error("Please enter an API Key in the sidebar.")
    else:
        with st.spinner("Architecting your SOW..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Generate a formal SOW for {solution_type} in the {industry} industry. Objective: {objective}. Outcomes: {outcomes}. Stakeholders: Partner ({p_name}), Customer ({c_name}). Maintain exact section numbering 1-7 as per enterprise standards."
                    }]
                }],
                "systemInstruction": {
                    "parts": [{
                        "text": "You are a senior GenAI Solution Architect. Output ONLY professional Markdown SOW content."
                    }]
                }
            }
            
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                sow_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                st.markdown("---")
                st.markdown(sow_text)
                st.download_button("Download SOW as TXT", sow_text, file_name="SOW.md")
            else:
                st.error("Failed to generate. Check your API Key or Network.")