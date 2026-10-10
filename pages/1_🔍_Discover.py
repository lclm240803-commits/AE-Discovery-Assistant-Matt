import streamlit as st
import pandas as pd
import json
import os
from openai import OpenAI
from utility import check_password

# ── 1. Page Configuration & Gatekeeper ────────────────────────
st.set_page_config(
    page_title="Discover AEs - AE Discovery Assistant",
    page_icon="🔍",
    layout="wide"
)

# Enforce access gatekeeper
if not check_password():
    st.stop()

st.title("🔍 Feature 1: Semantic Discovery of Adult Educators")
st.markdown(
    """
    Identify potential **Adult Educators (AEs)** by describing your course or engagement requirements 
    in natural language. The system grounds all recommendations strictly in documented synthetic records.
    """
)
st.markdown("---")

# ── 2. Data Loading with Caching ──────────────────────────────
@st.cache_data
def load_ae_dataset():
    excel_path = "SSI_AE_Mock_Dataset_100_Trainers.xlsx"
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path)
            return df
        except Exception:
            pass
            
    # Resilient fallback mock records if Excel has different sheet names
    fallback_data = [
        {
            "AE_ID": "AE-101",
            "Name": "Dr. Sarah Tan",
            "Domain_Expertise": "Youth Casework, Trauma-Informed Care, Counselling Psychology",
            "Sector_Experience": "Social Service Agencies, Youth Guidance Centres (12 years)",
            "Past_Courses": "Trauma-Informed Practice in Case Management; Youth Diversion Mentoring",
            "Avg_Rating": 4.85,
            "Specialist_Approaches": "Narrative Therapy, Trauma-Informed Supervision"
        },
        {
            "AE_ID": "AE-102",
            "Name": "Mark Lee",
            "Domain_Expertise": "Adaptive Leadership, Change Management, Cross-Sector Partnerships",
            "Sector_Experience": "Public Service Leadership, NCSS Collaborative Teams (15 years)",
            "Past_Courses": "Strategic Capability Transition; Leading Collaborative Transformation",
            "Avg_Rating": 4.62,
            "Specialist_Approaches": "Action Learning, Executive Coaching"
        },
        {
            "AE_ID": "AE-103",
            "Name": "Priya Nair",
            "Domain_Expertise": "Restorative Practices, Youth Mediation, Clinical Social Work",
            "Sector_Experience": "Family Service Centres, Youth Justice & Community Courts (10 years)",
            "Past_Courses": "Facilitating Restorative Dialogue with Adolescents; Ethical Casework",
            "Avg_Rating": 4.78,
            "Specialist_Approaches": "Restorative Justice Circles, Solution-Focused Brief Therapy"
        },
        {
            "AE_ID": "AE-104",
            "Name": "Jason Koh",
            "Domain_Expertise": "Disability Inclusion, Special Education, Assistive Technology",
            "Sector_Experience": "Adult Disability Homes, Special Education Institutes (8 years)",
            "Past_Courses": "Universal Design for Learning in Social Care; Practitioner Facilitation",
            "Avg_Rating": 4.70,
            "Specialist_Approaches": "Universal Design, Experiential Simulation"
        },
        {
            "AE_ID": "AE-105",
            "Name": "Fatima Rahman",
            "Domain_Expertise": "Elderly Mental Health, Dementia Care, Community Gerontology",
            "Sector_Experience": "Senior Activity Centres, Community Hospitals (11 years)",
            "Past_Courses": "Person-Centred Dementia Care; Gerontological Case Practice",
            "Avg_Rating": 4.90,
            "Specialist_Approaches": "Reminiscence Facilitation, Compassion-Focused Care"
        }
    ]
    return pd.DataFrame(fallback_data)

ae_df = load_ae_dataset()

# ── 3. Search Interface ───────────────────────────────────────
col_query, col_filters = st.columns([3, 1])

with col_query:
    default_prompt = st.session_state.get("last_requirement", "")
    user_requirement = st.text_area(
        "Enter Engagement / Training Requirements (Natural Language):",
        value=default_prompt,
        height=140,
        placeholder="e.g., Looking for an AE experienced in trauma-informed intervention and practical case facilitation for social service workers working with vulnerable youths."
    )

with col_filters:
    st.subheader("Search Guidance")
    st.caption("💡 The semantic retriever matches conceptual qualifications even if terms vary.")
    min_rating = st.slider("Filter by Minimum Historical Rating", 4.0, 5.0, 4.5, step=0.05)

find_clicked = st.button("🔎 Find Potentially Relevant AEs", type="primary")

# ── 4. Retrieval & Analysis Execution ─────────────────────────
if find_clicked:
    if not user_requirement.strip():
        st.warning("⚠️ Please provide training requirements before searching.")
    else:
        st.session_state["last_requirement"] = user_requirement
        
        # Prepare context representation from records
        records_summary = ae_df.to_dict(orient="records")
        context_str = json.dumps(records_summary, indent=2)

        # Retrieve OpenAI API Key from Streamlit Secrets
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        
        if not api_key:
            st.error("OpenAI API Key not found in Streamlit Secrets. Please configure `OPENAI_API_KEY`.")
        else:
            client = OpenAI(api_key=api_key)
            
            system_prompt = (
                "You are the Adult Educator (AE) Discovery Assistant for social service training officers.\n"
                "Your role is decision support ONLY. Follow these strict rules:\n"
                "1. Base all statements strictly on the provided AE records. Do NOT invent credentials or ratings.\n"
                "2. Identify the 2 to 3 most relevant AEs matching the requirement.\n"
                "3. For each candidate, provide:\n"
                "   - **AE Name & ID**\n"
                "   - **Documented Match Rationale**: Why their experience aligns with the need.\n"
                "   - **Relevant Sector Experience & Past Courses**\n"
                "   - **Historical Rating**\n"
                "   - **Information Gaps**: Explicitly state 'Not documented in available records' for any criteria not found.\n"
                "4. Maintain neutral tone: Never label any candidate as 'the best', 'winner', or 'selected'. Final choice belongs to the officer."
            )

            with st.spinner("Retrieving records and synthesizing evidence..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"AE Records:\n{context_str}\n\nTraining Requirement:\n{user_requirement}"}
                        ],
                        temperature=0.2
                    )
                    st.session_state["discovery_analysis"] = response.choices[0].message.content
                except Exception as e:
                    st.error(f"Error calling LLM: {e}")

# ── 5. Render Results & Shortlist Selection ───────────────────
if "discovery_analysis" in st.session_state:
    st.markdown("### 📋 Analysis & Grounded Evidence")
    st.markdown(st.session_state["discovery_analysis"])
    st.markdown("---")

    # Shortlisting for Comparison Workflow
    st.subheader("⚖️ Shortlist Candidates for Side-by-Side Comparison")
    st.caption("Select two or more candidates to compare on the **Compare** page.")
    
    candidate_options = ae_df["Name"].tolist()
    
    selected_aes = st.multiselect(
        "Select AEs to Shortlist:",
        options=candidate_options,
        default=st.session_state.get("selected_candidates", candidate_options[:2])
    )
    
    st.session_state["selected_candidates"] = selected_aes
    
    if len(selected_aes) >= 2:
        st.success(f"✅ {len(selected_aes)} candidates shortlisted! Head to the **2 ⚖️ Compare** page in the sidebar.")
    elif len(selected_aes) == 1:
        st.info("Select at least one more candidate for comparison.")
    else:
        st.warning("Please select at least 2 candidates to compare.")

with st.expander("📂 View Available AE Records (Raw Knowledge Base)"):
    st.dataframe(ae_df, use_container_width=True)