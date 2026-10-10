import streamlit as st
from utility import check_password
st.set_page_config(
    page_title="About Us - AE Discovery Assistant",
    page_icon="ℹ️",
    layout="wide"
)
if not check_password():
    st.stop()
st.title("ℹ️ About the AE Discovery & Comparison Assistant")
st.markdown("---")

# 1. Project Background & Context
st.header("1. Agency Context & Problem Statement")
st.markdown(
    """
    In public social service institutes and agencies (e.g., SSI / NCSS), training coordinators 
    and officers frequently need to identify suitable **Adult Educators (AEs)** for specialized, 
    practice-based courses. 
    
    **Current Challenges:**
    * **Manual Record Review:** Officers manually cross-reference voluminous curriculum vitae, 
      course outlines, and historical evaluation sheets.
    * **Vocabulary Mismatch:** Traditional keyword searches fail when training requirements 
      use terminology different from profile descriptions (e.g., *'vulnerable youths'* vs. 
      *'adolescents experiencing psychosocial difficulties'*).
    * **Inconsistent Comparisons:** Evaluating multiple candidates side-by-side against specific 
      facilitation parameters is time-consuming and subjective.
    """
)

# 2. Objectives
st.header("2. Project Objectives")
st.markdown(
    """
    The **AE Discovery & Comparison Assistant** is a proof-of-concept (POC) tool designed to:
    1. **Accelerate Discovery:** Use semantic search (RAG) to surface relevant AE profiles from natural-language descriptions.
    2. **Ground Every Claim:** Ensure every surfaced capability is tied directly to retrieved records, eliminating hallucinated credentials.
    3. **Facilitate Objective Comparison:** Allow side-by-side assessment across uniform criteria while explicitly flagging information gaps.
    4. **Preserve Human Discretion:** Act strictly as a decision-support tool—never auto-selecting or declaring a "best" candidate.
    """
)

# 3. Target Users & Scope
st.header("3. Target Audience & Scope Boundaries")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Target Audience")
    st.write("- Training Officers & Course Managers")
    st.write("- Capability Development Leads")
    st.write("- Agency Curriculum Designers")

with col2:
    st.subheader("Scope Boundaries")
    st.write("✅ **In Scope:** Natural-language discovery, multi-profile comparison, gap detection.")
    st.write("❌ **Out of Scope:** Automated booking, performance prediction, or definitive hiring decisions.")

# 4. Data Sources & Privacy
st.header("4. Data Sources & Privacy Governance")
st.markdown(
    """
    * **Synthetic Dataset:** To safeguard officer and instructor privacy in accordance with bootcamp policy, 
      this prototype uses **100% synthetic AE profiles and engagement records**.
    * **Data Schema:** Includes professional domain background, sector experience, service-user groups, 
      facilitation history, and anonymized post-course evaluation ratings.
    * **Confidentiality:** No real-world personal data or restricted civil service credentials are processed.
    """
)

# 5. Project Team
st.header("5. Project Team")
st.markdown(
    """
    Developed for the **AI Champions Bootcamp (Project Type 1 / Agency Track)**:
    * **Saiful** – Domain Lead & Requirements Engineering
    * **Matt** – Technical Architecture & Streamlit Engineering
    """
)

st.markdown("---")
st.caption("Adult Educator Discovery & Comparison Assistant · AI Champions Bootcamp 2026")