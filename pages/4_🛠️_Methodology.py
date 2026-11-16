import streamlit as st
from utility import check_password

st.set_page_config(
    page_title="Methodology - AE Discovery Assistant",
    page_icon="🛠️",
    layout="wide"
)

# Enforce access gatekeeper
if not check_password():
    st.stop()

st.title("🛠️ Methodology & Technical Implementation")
st.markdown("---")

st.markdown(
    """
    This page details the technical architecture, cloud database retrieval pipeline, prompt engineering 
    techniques, and safety guardrails powering the **AE Discovery & Comparison Assistant**.
    """
)

# 1. Use Case 1 Flowchart & Data Flow
st.header("1. Use Case 1: Semantic Discovery Architecture")
st.markdown(
    """
    Traditional keyword filters fail when training requirements use terminology different from profile descriptions. 
    Our discovery pipeline uses **Retrieval-Augmented Generation (RAG)** backed by **Supabase PostgreSQL** to retrieve 
    structured Adult Educator records (`AE-001` to `AE-100`) and perform full-context semantic matching and evidence grounding via `gpt-4o-mini`.
    """
)

st.subheader("Process Flowchart: Discovery")
st.graphviz_chart("""
digraph DiscoveryFlow {
    rankdir=LR;
    node [shape=box, style="rounded,filled", fillcolor="#F0F4F8", fontname="Helvetica"];
    
    User [label="Officer Requirement\\n(Natural-Language Input)", fillcolor="#D1E8FF"];
    SupabaseDB [label="Supabase PostgreSQL\\n(AE_Mock_Dataset: 100 Profiles)", shape=cylinder, fillcolor="#FFE6CC"];
    Loader [label="Cached API Data Loader\\n(Assigns AE-001 to AE-100 IDs)"];
    PromptEngine [label="Semantic Matching & Bridging\\n(gpt-4o-mini · temp=0.2)"];
    Guardrail [label="Domain & Scope Guardrail\\n(In-Scope vs Out-of-Scope Check)"];
    Output [label="Grounded Shortlist +\\nSource Record Verification Cards", fillcolor="#D4EDDA"];

    SupabaseDB -> Loader;
    User -> Guardrail;
    Loader -> PromptEngine;
    Guardrail -> PromptEngine;
    PromptEngine -> Output;
}
""")

st.markdown(
    """
    **Key Steps in Discovery:**
    1. **Cloud Database Retrieval:** The application queries all 100 structured AE profiles live from Supabase PostgreSQL (`AE_Mock_Dataset`) via the REST API (cached via `@st.cache_data`) and tags each record with a traceable `Record_ID` (`AE-001` to `AE-100`).
    2. **Semantic Matching & Domain Bridging:** Rather than relying on brittle keyword matching or lossy chunk cutoffs, the structured profiles are passed into `gpt-4o-mini` (`temperature=0.2`), which maps natural-language needs and adjacent care terminology to the relevant social service sub-sectors.
    3. **Traceable Evidence Grounding:** Each recommended candidate is output alongside their exact `Record_ID`, verbatim `Domain_Expertise` field, and an expandable **Source Record Verification Panel** extracted directly from Supabase.
    """
)

st.markdown("---")

# 2. Use Case 2 Flowchart & Data Flow
st.header("2. Use Case 2: Requirement-Based Comparison & Gap Analysis")
st.markdown(
    """
    Once candidates are shortlisted on the Discover page (or selected manually), the system joins their 
    competency profiles with their historical course engagement records from Supabase to perform a uniform, 
    three-tier requirement alignment assessment.
    """
)

st.subheader("Process Flowchart: Comparison")
st.graphviz_chart("""
digraph ComparisonFlow {
    rankdir=LR;
    node [shape=box, style="rounded,filled", fillcolor="#F0F4F8", fontname="Helvetica"];
    
    Session [label="Shortlisted AEs & Requirement\\n(st.session_state Hand-off)", fillcolor="#D1E8FF"];
    SupabaseTables [label="Supabase PostgreSQL\\n(AE_Mock_Dataset + AE_Engagement)", shape=cylinder, fillcolor="#FFE6CC"];
    Joiner [label="Relational Record Joiner\\n(Profile + Past Course Runs)"];
    Classifier [label="3-Tier Classification Engine\\n(gpt-4o-mini · temp=0.1)"];
    Matrix [label="Requirement Alignment Matrix +\\nCited Explanations & Gaps", fillcolor="#D4EDDA"];

    Session -> Joiner;
    SupabaseTables -> Joiner;
    Joiner -> Classifier -> Matrix;
}
""")

st.markdown(
    """
    **Key Steps in Comparison:**
    1. **Relational Evidence Aggregation:** For each selected AE, the system retrieves their profile (`AE_Mock_Dataset`) and cross-references all historical courses taught (`AE_Engagement`, e.g., `ENG-0001`).
    2. **Three-Tier Requirement Alignment Matrix:** Evaluates candidates across uniform requirement rows using three strict classifications:
       * 🟢 **Documented:** Direct evidence in the AE's profile or qualifications establishes the requirement.
       * 🟡 **Related evidence:** Relevant course runs or adjacent experience exist (e.g., classroom delivery or motivational interviewing), but do not automatically establish full formal qualification.
       * ⚪ **Not documented:** Available records do not establish the requirement.
    3. **Domain Calibration & Neutral Decision Support:** Recognizes Singapore WSQ adult education standards (treating **ACTA** and **ACLP** as holding equal national recognition) and highlights trade-offs and verification questions without ever declaring a "best" candidate.
    """
)

st.markdown("---")

# 3. Prompt Engineering & Guardrails
st.header("3. Prompt Engineering & Safety Controls")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Prompt Engineering Techniques")
    st.markdown(
        """
        * **Structured JSON Context Injection:** Supabase records are serialized into compact JSON objects with explicit `Record_ID` and `Engagement_ID` keys for deterministic field citation.
        * **Role & Classification Constraints:** Low temperature settings (`0.1`–`0.2`) and strict formatting templates enforce consistent Markdown tables and badge classifications.
        * **Two-Stage Workflow Separation:** Discovery and Comparison use dedicated, task-specific system prompts connected via `st.session_state`.
        """
    )

with col2:
    st.subheader("Safety & Anti-Exploitation Controls")
    st.markdown(
        """
        * **Strict Grounding & Anti-Hallucination:** Explicit rules forbid inventing credentials, experience, or ratings; unverified criteria must be flagged as `⚪ Not documented`.
        * **Out-of-Scope Domain Rejection:** Non-human-service queries (e.g., civil engineering, aviation, finance) trigger the `NO_RELEVANT_DOMAIN` guardrail rather than forcing arbitrary matches.
        * **No Automatic Selection:** The assistant is prohibited from naming a "winner" or "best" AE, preserving human officer discretion.
        * **Access & Credential Security:** Protected by `check_password()` gatekeeper and server-side Streamlit Secrets (`SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY`).
        """
    )

st.markdown("---")

# 4. Mandatory POC Disclaimer
st.header("4. Deployment & Compliance Notice")
with st.expander("⚠️ View Proof-of-Concept Compliance Disclaimer (Mandatory)", expanded=True):
    st.warning(
        """
        **IMPORTANT NOTICE:** This web application is developed as a proof-of-concept prototype. 
        The information provided here is **NOT intended for actual usage** and should not be relied upon 
        for making any decisions, especially those related to financial, legal, or healthcare matters.

        Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. 
        You assume full responsibility for how you use any generated output. Always consult with qualified 
        professionals for accurate and personalised advice.
        """
    )

st.caption("Adult Educator Discovery & Comparison Assistant · AI Champions Bootcamp 2026")
