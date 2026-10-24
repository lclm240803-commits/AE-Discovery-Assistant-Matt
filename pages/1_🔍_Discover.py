import streamlit as st
import json
from openai import OpenAI
from supabase import create_client
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
st.caption("AI-Assisted Capability Matching · Decision Support for Training Officers")
st.markdown("---")

# ── 2. Supabase Cloud Database Loader ─────────────────────────
@st.cache_data(ttl=600)
def load_all_ae_records():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    # Query all 100 Adult Educator records from AE_Mock_Dataset in Supabase
    response = supabase.table("AE_Mock_Dataset").select("*").execute()
    records = []
    
    for row in response.data:
        records.append({
            "Name": row.get("Full Name") or "Unknown",
            "Agency_or_Org": row.get("Organisation") or "Social Service Institute",
            "Designation": row.get("Designation") or "Adult Educator",
            "Sub_Sector": row.get("Sub-Sector") or "General",
            "Expertise": row.get("Domain Expertise") or "General Facilitation",
            "Qualifications": row.get("Highest Academic Qualifications") or "Professional Degree",
            "Sector_Exp_Yrs": str(row.get("Years in Social Service Sector/Relevant Sector") or "10"),
            "Training_Exp_Yrs": str(row.get("Training Experience") or "5"),
            "ACTA_Certified": row.get("ACTA/ACLP Certified") or "Yes",
            "Avg_Rating": str(row.get("Ave AE effectiveness in FY25") or "4.8")
        })
    return records

ae_records = load_all_ae_records()
candidate_options = [r["Name"] for r in ae_records]

# ── Session State Management (Cross-Page Persistent) ─────────
if "selected_candidates" not in st.session_state:
    st.session_state["selected_candidates"] = []

if "discover_picker" not in st.session_state:
    st.session_state["discover_picker"] = [
        name for name in st.session_state["selected_candidates"] if name in candidate_options
    ]

# ── 3. Search & Input Section ─────────────────────────────────
st.subheader("1. Training Requirement Input")
col_query, col_info = st.columns([3, 1])

with col_query:
    default_prompt = st.session_state.get("last_requirement", "")
    user_requirement = st.text_area(
        "Describe your course objectives, target audience, or desired competencies:",
        value=default_prompt,
        height=130,
        placeholder="e.g., Seeking an experienced trainer with a clinical or social work background in trauma-informed care and counselling for youth-at-risk caseworkers."
    )
    
    col_btn1, col_btn2 = st.columns([3, 2])
    with col_btn1:
        find_clicked = st.button("🔎 Search Relevant Adult Educators", type="primary", use_container_width=True)
    with col_btn2:
        reset_clicked = st.button("🔄 Clear / Reset Search", use_container_width=True)

    # ── Reset / Clean Slate Logic ─────────────────────────────
    if reset_clicked:
        st.session_state["last_requirement"] = ""
        st.session_state["selected_candidates"] = []
        st.session_state["discover_picker"] = []
        st.session_state["ai_suggested_candidates"] = []
        if "compare_picker" in st.session_state:
            st.session_state["compare_picker"] = []
        if "discovery_analysis" in st.session_state:
            del st.session_state["discovery_analysis"]
        if "last_comparison_text" in st.session_state:
            del st.session_state["last_comparison_text"]
        st.rerun()

with col_info:
    with st.container(border=True):
        st.markdown("**Cloud Database Scope**")
        st.metric("Total AE Profiles", len(ae_records))
        st.caption("Live PostgreSQL records fetched via Supabase API.")

# ── 4. Retrieval & Analysis Execution ─────────────────────────
if find_clicked:
    if not user_requirement.strip():
        st.warning("⚠️ Please enter a training requirement before searching.")
    else:
        st.session_state["last_requirement"] = user_requirement
        
        context_str = json.dumps(ae_records[:35], indent=2)
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        
        if not api_key:
            st.error("OpenAI API Key not found. Please configure `OPENAI_API_KEY` in Streamlit Cloud Settings → Secrets.")
        else:
            client = OpenAI(api_key=api_key)
            
            system_prompt = (
                "You are the Adult Educator (AE) Discovery Assistant for public social service training officers.\n"
                "Your role is decision support ONLY. Follow these strict domain & grounding rules:\n\n"
                "RULE 1: MANDATORY SEMANTIC BRIDGING FOR CARE, COMMUNITY & HUMAN SERVICES\n"
                "- ALL caregiving, health & wellness support, end-of-life care, and psychosocial topics ARE WITHIN THE SOCIAL SERVICE SCOPE. You MUST bridge them to available sub-sectors:\n"
                "  • 'Palliative care' / 'End-of-life' / 'Hospice' / 'Bereavement' / 'Grief' -> Semantically bridge to Mental Health & Caregiving (caregiver support, suicide/crisis intervention, de-escalation) or Family (caregiver engagement).\n"
                "  • 'Eldercare' / 'Gerontology' / 'Dementia' / 'Aging' -> Semantically bridge to Mental Health & Caregiving or Family (caregiver support).\n"
                "  • 'Infant care' / 'Early childhood' / 'Babies' -> Semantically bridge to Foster Parents (attachment, trauma-informed caregiving) or Family (parenting).\n"
                "  • 'Youth crime' / 'Delinquency' / 'School refusal' -> Semantically bridge to Children & Youth.\n"
                "- When bridging, ALWAYS identify the 2 to 3 closest Adult Educators from that bridged sub-sector.\n"
                "- If the user requests high years of experience (e.g. 20+ or 30+ years), surface the most senior available trainers in that bridged domain (e.g., senior trainers with 15-26 years training exp and 20-30 years sector exp). DO NOT reject the query; simply explain the experience difference in 'Documented Match Rationale' and note the 30-year requirement in 'Information Gaps'.\n"
                "- Format each candidate strictly as:\n"
                "   Candidate X: [Exact Full Name]\n"
                "   - **Candidate Name & Designation**: [Exact Full Name], [Designation]\n"
                "   - **Sub-Sector Alignment**: [Alignment]\n"
                "   - **Documented Match Rationale**: [Reasoning, including semantic bridge explanation]\n"
                "   - **Years of Training Experience & Historical Effectiveness Rating**: [Exp], [Rating]\n"
                "   - **Information Gaps**: [Gaps or 'Not documented in available records']\n\n"
                "RULE 2: STRICT REJECTION FOR NON-HUMAN SERVICES ONLY\n"
                "- If and ONLY if the user's query asks for an entirely unrelated, non-human-services technical or industrial domain (e.g., Civil/Mechanical Engineering, Artificial Intelligence/Machine Learning, Computer Hardware, Aviation, Construction, Finance/Accounting, Real Estate Sales):\n"
                "  1. Start your response with 'NO_RELEVANT_DOMAIN'.\n"
                "  2. State clearly that the requested field is a technical/commercial discipline outside the social service training scope.\n"
                "  3. Do NOT recommend, name, or shortlist ANY candidates.\n"
                "  4. Explicitly state this in 'Information Gaps'.\n\n"
                "RULE 3: NEUTRAL DECISION SUPPORT\n"
                "- Never declare any candidate as 'the best' or 'winner'."
            )

            with st.spinner("Analyzing AE profiles and synthesizing evidence..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"AE Records:\n{context_str}\n\nOfficer Training Requirement:\n{user_requirement}"}
                        ],
                        temperature=0.2
                    )
                    analysis_text = response.choices[0].message.content
                    st.session_state["discovery_analysis"] = analysis_text
                    
                    # ── Robust Name Detection ──────────────────────────────
                    extracted_names = []
                    if "NO_RELEVANT_DOMAIN" not in analysis_text:
                        found_candidates = []
                        for real_name in candidate_options:
                            pos = analysis_text.find(real_name)
                            if pos != -1:
                                found_candidates.append((pos, real_name))
                        
                        found_candidates.sort(key=lambda x: x[0])
                        for _, name in found_candidates:
                            if name not in extracted_names:
                                extracted_names.append(name)
                    
                    st.session_state["ai_suggested_candidates"] = extracted_names[:3]

                except Exception as e:
                    st.error(f"Error calling LLM: {e}")

# ── 5. Render Discovery Results (If Search Run) ───────────────
if "discovery_analysis" in st.session_state:
    st.markdown("---")
    st.subheader("2. AI Discovery Analysis & Evidence")
    
    with st.container(border=True):
        clean_display = st.session_state["discovery_analysis"].replace("NO_RELEVANT_DOMAIN", "").lstrip(". \n").strip()
        st.markdown(clean_display)
        
    ai_suggestions = st.session_state.get("ai_suggested_candidates", [])
    
    if not ai_suggestions:
        st.warning("⚠️ **No matching Adult Educators found in the records for these criteria.** The requested domain is outside social service records. Try adjusting your requirements (e.g., searching for *Children & Youth*, *Family*, *Disability*, or *Mental Health*), or manually pick candidates below.")
    else:
        st.markdown("---")
        with st.container(border=True):
            st.markdown("#### 🎯 Would you like to select the shortlisted candidates for comparison?")
            st.write(f"Recommended: **{', '.join(ai_suggestions)}**")
            
            c_yes, c_no, _ = st.columns([1, 1, 2])
            with c_yes:
                if st.button("✅ Yes, proceed to Compare", type="primary", use_container_width=True):
                    st.session_state["selected_candidates"] = ai_suggestions
                    st.session_state["discover_picker"] = ai_suggestions
                    if "compare_picker" in st.session_state:
                        st.session_state["compare_picker"] = ai_suggestions
                    st.switch_page("pages/2_⚖️_Compare.py")
            with c_no:
                if st.button("❌ No, start new search", use_container_width=True):
                    st.session_state["last_requirement"] = ""
                    st.session_state["selected_candidates"] = []
                    st.session_state["discover_picker"] = []
                    st.session_state["ai_suggested_candidates"] = []
                    if "compare_picker" in st.session_state:
                        st.session_state["compare_picker"] = []
                    if "discovery_analysis" in st.session_state:
                        del st.session_state["discovery_analysis"]
                    if "last_comparison_text" in st.session_state:
                        del st.session_state["last_comparison_text"]
                    st.rerun()

# ── 6. Candidate Shortlisting for Compare Page (Always Visible) ─
st.markdown("---")
st.subheader("3. Shortlist Candidates for Comparison")
st.caption("Selected candidates will be carried over to the **2 ⚖️ Compare** page.")

def sync_discover_candidates():
    st.session_state["selected_candidates"] = st.session_state["discover_picker"]

selected_aes = st.multiselect(
    "Select at least 2 Adult Educators to compare side-by-side:",
    options=candidate_options,
    key="discover_picker",
    on_change=sync_discover_candidates,
    placeholder="Choose Adult Educators from recommendations or directory..."
)
st.session_state["selected_candidates"] = selected_aes

if len(selected_aes) >= 2:
    st.success(f"✅ **{len(selected_aes)} candidates shortlisted!** You can now proceed to the **2 ⚖️ Compare** page in the left sidebar.")
else:
    st.info("ℹ️ Select at least 2 candidates to enable full comparative analysis.")

# ── 7. Enhanced Profile Explorer (Natural Cards) ──────────────
st.markdown("---")
with st.expander("👤 Browse Adult Educator Profiles Directory", expanded=False):
    st.caption("Search or preview trainer credentials from the Supabase knowledge base.")
    
    search_filter = st.text_input("Filter profiles by name or keyword:", placeholder="e.g. Tan Wei Ming, Youth, Trauma...")
    
    displayed_records = ae_records
    if search_filter:
        displayed_records = [
            r for r in ae_records
            if search_filter.lower() in r["Name"].lower() or search_filter.lower() in r["Expertise"].lower() or search_filter.lower() in r["Sub_Sector"].lower()
        ]

    for profile in displayed_records[:8]:
        with st.container(border=True):
            col_main, col_stats = st.columns([3, 1])
            with col_main:
                st.markdown(f"### {profile['Name']}")
                st.markdown(f"**{profile['Designation']}** · *{profile['Agency_or_Org']}*")
                st.markdown(f"**🏷️ Sub-Sector:** `{profile['Sub_Sector']}`")
                st.markdown(f"**🎯 Specialisation / Expertise:** {profile['Expertise']}")
                st.caption(f"🎓 Qualifications: {profile['Qualifications']} | ACTA/ACLP: {profile['ACTA_Certified']}")
            with col_stats:
                st.metric("Avg Effectiveness", f"⭐ {profile['Avg_Rating']}/5.0")
                st.metric("Training Exp.", f"{profile['Training_Exp_Yrs']} yrs")
