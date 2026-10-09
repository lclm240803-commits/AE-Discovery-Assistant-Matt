import streamlit as st

st.set_page_config(
    page_title="Methodology - AE Discovery Assistant",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ Methodology & Technical Implementation")
st.markdown("---")

st.markdown(
    """
    This page details the technical architecture, data processing pipeline, prompt engineering 
    techniques, and safety guardrails powering the **AE Discovery & Comparison Assistant**.
    """
)

# 1. Use Case 1 Flowchart & Data Flow
st.header("1. Use Case 1: Semantic Discovery Architecture")
st.markdown(
    """
    Traditional lexical queries fail when domain synonyms differ. Our discovery pipeline uses 
    **Retrieval-Augmented Generation (RAG)** to connect natural-language requirements with synthetic AE profiles.
    """
)

st.subheader("Process Flowchart: Discovery")
st.graphviz_chart("""
digraph DiscoveryFlow {
    rankdir=LR;
    node [shape=box, style="rounded,filled", fillcolor="#F0F4F8", fontname="Helvetica"];
    
    User [label="Officer Requirement\\n(Free-text prompt)", fillcolor="#D1E8FF"];
    Extract [label="LLM Requirement\\nExtractor (Prompt 1)"];
    Embed [label="Text Embeddings\\n(text-embedding-3-small)"];
    VectorStore [label="Vector Store / Records\\n(Synthetic AE Data)", shape=cylinder, fillcolor="#FFE6CC"];
    Retriever [label="Top-k Retrieval\\n(Semantic Match)"];
    GroundedLLM [label="Grounded Synthesis\\n(Prompt 2 + Context)"];
    Cards [label="Evidence Cards &\\nRelevance Summaries", fillcolor="#D4EDDA"];

    User -> Extract -> Embed -> Retriever;
    VectorStore -> Retriever;
    Retriever -> GroundedLLM;
    GroundedLLM -> Cards;
}
""")

st.markdown(
    """
    **Key Steps in Discovery:**
    1. **Requirement Extraction:** The raw input is parsed into target population, domain expertise, and facilitation constraints without adding external assumptions.
    2. **Vector Retrieval:** The extracted query is embedded and matched against pre-indexed synthetic profile chunks using similarity search.
    3. **Grounded Synthesis:** The model explains why each candidate aligns based *only* on retrieved passages, citing record IDs.
    """
)

st.markdown("---")

# 2. Use Case 2 Flowchart & Data Flow
st.header("2. Use Case 2: Structured Comparison & Gap Analysis")
st.markdown(
    """
    Once candidates are shortlisted, officers select 2–3 profiles. The system extracts comparable metrics 
    directly against the initial training context.
    """
)

st.subheader("Process Flowchart: Comparison")
st.graphviz_chart("""
digraph ComparisonFlow {
    rankdir=LR;
    node [shape=box, style="rounded,filled", fillcolor="#F0F4F8", fontname="Helvetica"];
    
    Selected [label="Selected AEs\\n(Session State)", fillcolor="#D1E8FF"];
    Context [label="Original Requirement\\n(Retained Context)"];
    FetchRecords [label="Profile & Engagement\\nRecord Aggregator"];
    CompareLLM [label="Comparison Engine\\n(Prompt Chain 3)"];
    OutputTable [label="Side-by-Side Matrix +\\nInformation Gaps", fillcolor="#D4EDDA"];

    Selected -> FetchRecords;
    Context -> CompareLLM;
    FetchRecords -> CompareLLM -> OutputTable;
}
""")

st.markdown(
    """
    **Key Steps in Comparison:**
    1. **Context Retention:** `st.session_state` preserves the original requirement so comparison evaluates fitness for the specific task.
    2. **Uniform Evaluation Criteria:** Assesses domain fit, sector depth, target audience experience, and evaluation trends.
    3. **Explicit Gap Detection:** Any missing profile field is strictly labeled **"Not documented in available records"** rather than assumed positive.
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
        * **Delimiter Isolation:** Triple backticks and XML tags separate system instructions from user-provided inputs.
        * **Few-Shot Grounding:** In-context examples guide the LLM to format responses into structured bullet points with explicit source references.
        * **Prompt Chaining:** Discovery and comparison are separated into discrete prompt stages to minimize cognitive load and eliminate context drift.
        """
    )

with col2:
    st.subheader("Safety & Anti-Exploitation Controls")
    st.markdown(
        """
        * **No-Invention Directive:** Explicit instructions forbid inferring unstated qualifications, years of experience, or personal attributes.
        * **No Automatic Winner:** The system is constrained never to output titles like *"Best Candidate"* or *"Winner"*, enforcing officer ownership.
        * **Prompt Injection Resilience:** Instructions inside documents or user inputs attempting to override base policies (e.g., *"Ignore previous rules"*) are ignored.
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