import streamlit as st

st.set_page_config(
    page_title="AE Discovery & Comparison Assistant",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Adult Educator Discovery & Comparison Assistant")
st.subheader("Proof-of-Concept Prototype")

# Mandatory Disclaimer as required by the bootcamp assessment rubric
with st.expander("⚠️ IMPORTANT NOTICE (Please Read Before Use)", expanded=True):
    st.warning(
        """
        **IMPORTANT NOTICE:** This web application is developed as a proof-of-concept prototype. 
        The information provided here is **NOT intended for actual usage** and should not be relied upon 
        for making any decisions, especially those related to financial, legal, or healthcare matters.

        Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. 
        You assume full responsibility for how you use any generated output. 
        Always consult with qualified professionals for accurate and personalised advice.
        """
    )

st.markdown(
    """
    ### Welcome!
    This tool assists training officers in discovering and comparing potentially relevant 
    Adult Educators (AEs) based on documented competencies, sector experience, and past evaluations.

    **Explore using the sidebar menu on the left:**
    - **1 🔍 Discover:** Natural-language search for AE profiles.
    - **2 ⚖️ Compare:** Objective side-by-side comparison across shortlisted candidates.
    - **3 ℹ️ About Us:** Detailed project background, objectives, and team roles.
    - **4 🛠️ Methodology:** Technical architecture, RAG flowcharts, and safety controls.
    """
)