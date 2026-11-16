import streamlit as st
import json
from openai import OpenAI
from supabase import create_client
from utility import check_password

# ── 1. Page Configuration & Gatekeeper ────────────────────────
st.set_page_config(
    page_title="Compare AEs - AE Discovery Assistant",
    page_icon="⚖️",
    layout="wide"
)

# Enforce access gatekeeper
if not check_password():
    st.stop()

st.title("⚖️ Feature 2: Objective Side-by-Side AE Comparison")
st.caption("Evidence-Based Evaluation · Requirement Alignment Matrix · Gap Analysis")
st.markdown("---")

# Helper to safely read column values regardless of slight header variations in Supabase
def get_col(row, possible_keys, default_val):
    for k in possible_keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    row_lower = {str(k).strip().lower(): v for k, v in row.items() if v not in (None, "")}
    for k in possible_keys:
        k_low = k.strip().lower()
        if k_low in row_lower:
            return row_lower[k_low]
    return default_val

# ── 2. Cloud Database Loaders (Supabase External Storage) ──────
@st.cache_data(ttl=600)
def load_trainer_profiles():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    response = supabase.table("AE_Mock_Dataset").select("*").execute()
    records = []
    for idx, row in enumerate(response.data, start=1):
        name_val = get_col(row, ["Full Name", "Name", "Trainer Name", "AE Name"], "Unknown")
        org_val = get_col(row, ["Organisation", "Organization", "Agency", "Agency_or_Org"], "Social Service Institute")
        desig_val = get_col(row, ["Designation", "Role", "Title"], "Adult Educator")
        subsector_val = get_col(row, ["Sub-Sector", "Sub_Sector", "Sub Sector", "Subsector", "Sector"], "Social Service")
        exp_val = get_col(row, ["Domain Expertise", "Area of Specialisation / Core Expertise", "Expertise", "Specialisation"], "General Facilitation")
        qual_val = get_col(row, ["Highest Academic Qualifications", "Qualifications", "Academic Qualifications"], "Professional Degree")
        sec_yrs = get_col(row, ["Years in Social Service Sector/Relevant Sector", "Sector_Exp_Yrs", "Sector Experience"], "N/A")
        trn_yrs = get_col(row, ["Training Experience", "Training_Exp_Yrs", "Years of Training Experience"], "N/A")
        acta_val = get_col(row, ["ACTA/ACLP Certified", "ACTA_Certified", "ACTA/ACLP"], "Not documented")
        rating_val = get_col(row, ["Ave AE effectiveness in FY25", "Avg_Rating", "AE Effectiveness"], "4.8")

        records.append({
            "Record_ID": f"AE-{idx:03d}",
            "Source_Table": f"Supabase: AE_Mock_Dataset (Row {idx})",
            "Name": str(name_val),
            "Agency_or_Org": str(org_val),
            "Designation": str(desig_val),
            "Sub_Sector": str(subsector_val),
            "Expertise": str(exp_val),
            "Qualifications": str(qual_val),
            "Sector_Exp_Yrs": str(sec_yrs),
            "Training_Exp_Yrs": str(trn_yrs),
            "ACTA_Certified": str(acta_val),
            "Avg_Rating": str(rating_val)
        })
    return records

@st.cache_data(ttl=600)
def load_engagement_history():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    response = supabase.table("AE_Engagement").select("*").execute()
    engagements = []
    for row in response.data:
        engagements.append({
            "Engagement_ID": str(get_col(row, ["Engagement ID", "Engagement_ID"], "")),
            "Sub_Sector": str(get_col(row, ["Sub-Sector", "Sub_Sector", "Sub Sector"], "")),
            "Course_Title": str(get_col(row, ["Course Title", "Course_Title"], "")),
            "Delivery_Mode": str(get_col(row, ["Mode of Delivery", "Delivery_Mode"], "")),
            "AE_1": str(get_col(row, ["Fictional AE 1", "AE_1"], "")),
            "AE_2": str(get_col(row, ["Fictional AE 2", "AE_2"], "")),
            "AE_3": str(get_col(row, ["Fictional AE 3", "AE_3"], ""))
        })
    return engagements

try:
    trainers = load_trainer_profiles()
    engagements = load_engagement_history()
except Exception as e:
    st.error(f"Error connecting to Supabase database: {e}")
    trainers = []
    engagements = []

trainer_map = {t["Name"]: t for t in trainers}
all_names = [t["Name"] for t in trainers]

# Helper to find engagements for a trainer
def get_trainer_courses(trainer_name):
    matched_courses = []
    for eng in engagements:
        trainers_in_row = [eng["AE_1"], eng["AE_2"], eng["AE_3"]]
        if any(trainer_name.lower() in t.lower() for t in trainers_in_row if t):
            matched_courses.append({
                "Engagement_ID": eng["Engagement_ID"],
                "Course_Title": eng["Course_Title"],
                "Sub_Sector": eng["Sub_Sector"],
                "Delivery_Mode": eng["Delivery_Mode"]
            })
    return matched_courses

# ── 3. Active Context & Selection ─────────────────────────────
officer_requirement = st.session_state.get("last_requirement", "")
shortlisted = st.session_state.get("selected_candidates", [])

st.subheader("1. Comparison Context & Candidate Selection")
col_context, col_pick = st.columns([2, 1])

with col_context:
    with st.container(border=True):
        st.markdown("**Stated Training Need / Objective:**")
        if officer_requirement:
            st.info(f"📌 *\"{officer_requirement}\"*")
        else:
            st.caption("No custom requirement carried from Discover page. You can enter or modify candidates on the right to compare.")

with col_pick:
    default_selection = [name for name in shortlisted if name in all_names]
    if "compare_picker" not in st.session_state:
        st.session_state["compare_picker"] = default_selection

    def sync_compare_candidates():
        st.session_state["selected_candidates"] = st.session_state["compare_picker"]
        st.session_state["discover_picker"] = st.session_state["compare_picker"]

    selected_aes = st.multiselect(
        "Shortlisted Adult Educators:",
        options=all_names,
        default=default_selection,
        key="compare_picker",
        on_change=sync_compare_candidates
    )
    st.session_state["selected_candidates"] = selected_aes

# ── 4. Structured Side-by-Side Comparison Matrix ─────────────
st.markdown("---")
st.subheader("2. Structured Profile & Engagement Evidence Matrix")

if len(selected_aes) < 2:
    st.info(
        "ℹ️ **No candidates shortlisted for comparison yet.**\n\n"
        "Please go to the **🔍 Discover** page to search and shortlist candidates, "
        "or select at least **2 Adult Educators** from the dropdown above to view the side-by-side evidence matrix."
    )
else:
    cols = st.columns(len(selected_aes))

    for i, ae_name in enumerate(selected_aes):
        profile = trainer_map.get(ae_name, None)
        past_courses = get_trainer_courses(ae_name)
        
        with cols[i]:
            with st.container(border=True):
                if profile:
                    st.markdown(f"### {profile['Record_ID']} · {ae_name}")
                    st.caption(f"{profile['Designation']} · {profile['Agency_or_Org']} | Source: {profile['Source_Table']}")
                    st.markdown(f"**🏷️ Sub-Sector:** `{profile['Sub_Sector']}`")
                    
                    m1, m2 = st.columns(2)
                    with m1:
                        st.metric("Avg Rating", f"⭐ {profile['Avg_Rating']}/5.0")
                    with m2:
                        st.metric("Training Exp.", f"{profile['Training_Exp_Yrs']} yrs")
                    
                    st.markdown("---")
                    st.markdown(f"**🎯 Specialisation:**\n{profile['Expertise']}")
                    st.markdown(f"**🎓 Academic Qualifications:**\n{profile['Qualifications']}")
                    st.markdown(f"**📜 ACTA/ACLP:** `{profile['ACTA_Certified']}`")
                    st.markdown(f"**🏢 Sector Exp:** {profile['Sector_Exp_Yrs']} yrs")

                    st.markdown("---")
                    st.markdown(f"**📚 Documented Course Runs ({len(past_courses)} found):**")
                    if past_courses:
                        for c in past_courses[:4]:
                            st.markdown(f"- **`{c['Engagement_ID']}`**: {c['Course_Title']}")
                            st.caption(f"  Sector: {c['Sub_Sector']} | Mode: {c['Delivery_Mode']}")
                    else:
                        st.caption("No specific course engagements found in current records.")
                else:
                    st.error("Profile not found.")

    # ── 5. AI Requirement-Based Comparison Matrix & Gap Analysis ──
    st.markdown("---")
    st.subheader("3. Requirement-Based Comparison Matrix & Gap Analysis")
    
    with st.container(border=True):
        st.markdown("**Classification Legend (Evidence Verification Standard):**")
        leg1, leg2, leg3 = st.columns(3)
        with leg1:
            st.markdown("🟢 **Documented**\nDirect evidence in the AE's profile or qualifications explicitly establishes the requirement.")
        with leg2:
            st.markdown("🟡 **Related evidence**\nRelevant course runs or adjacent experience exist, but do not automatically establish full qualification or competence in the requirement.")
        with leg3:
            st.markdown("⚪ **Not documented**\nAvailable profile and engagement records do not establish the requirement.")

    compare_btn = st.button("📊 Run Requirement-Based Comparative Analysis", type="primary", use_container_width=True)

    if compare_btn or "last_comparison_text" in st.session_state:
        if compare_btn:
            comparison_payload = []
            for name in selected_aes:
                p = trainer_map.get(name, {}).copy()
                p["Documented_Course_Runs"] = get_trainer_courses(name)[:6]
                comparison_payload.append(p)
                
            context_str = json.dumps(comparison_payload, indent=2)
            req_context = officer_requirement if officer_requirement else "General social service practitioner training, domain expertise alignment, counselling/clinical background, and practice-based facilitation."
            api_key = st.secrets.get("OPENAI_API_KEY", "")
            
            if not api_key:
                st.error("OpenAI API Key not found. Please verify OPENAI_API_KEY in Streamlit Cloud Settings → Secrets.")
            else:
                client = OpenAI(api_key=api_key)
                system_prompt = (
                    "You are an objective decision-support assistant for public social service training officers.\n"
                    "Your task is to evaluate and compare the shortlisted Adult Educators side-by-side against the officer's training requirements using a strict 3-tier evidence classification standard.\n\n"
                    "STRICT EVIDENCE CLASSIFICATION DEFINITIONS:\n"
                    "- **Documented**: Direct, explicit evidence in the AE's profile (e.g., stated Domain Expertise, Sub-Sector, or Academic Qualifications) directly establishes the requirement.\n"
                    "- **Related evidence**: Relevant or adjacent experience exists (e.g., conducting related course runs, holding ACTA/ACLP pedagogical certification, or having related skills like motivational interviewing), but it does NOT automatically establish a formal qualification or guaranteed competence in the specific requirement (for example, conducting a classroom course or holding ACTA provides related evidence for practice-based facilitation, and motivational interviewing provides related evidence for counselling, but neither automatically establishes formal clinical counselling qualification).\n"
                    "- **Not documented**: Available profile and engagement records do not establish the requirement.\n\n"
                    "REQUIRED OUTPUT FORMAT:\n"
                    "### 1. Training Requirement Alignment Matrix\n"
                    "- Break the officer's training requirement down into 3 to 5 distinct evaluation rows (e.g., Target Population / Sector Experience, Specific Domain / Clinical / Counselling Background, Practice-Based Facilitation Competence, Pedagogical Certification / Tenure).\n"
                    "- Output a clean Markdown table with columns: `Requirement` | `[Candidate 1 Name (Record_ID)]` | `[Candidate 2 Name (Record_ID)]` (and Candidate 3 if present).\n"
                    "- Every cell under a candidate column MUST contain ONLY one of the three exact classification labels: **`Documented`**, **`Related evidence`**, or **`Not documented`**.\n\n"
                    "### 2. Classification Explanations & Source Evidence Traceability\n"
                    "- For each requirement row in the table, provide a concise bulleted explanation justifying the classification assigned to each candidate.\n"
                    "- Explicitly cite the candidate's `Record_ID` (e.g., AE-001), exact `Expertise` or `Qualifications` field, and specific `Engagement_ID` (e.g., ENG-0071) or `Course_Title` where applicable.\n"
                    "- Clearly explain why any `Related evidence` classification is partial rather than fully `Documented`.\n\n"
                    "### 3. Key Trade-Offs & Information Gaps to Verify\n"
                    "- Summarize key trade-offs across the candidates and list specific questions or unverified areas the training officer should confirm before making an engagement decision.\n"
                    "- Maintain a neutral decision-support tone: NEVER declare a 'winner', 'best candidate', or 'recommended choice'."
                )

                with st.spinner("Evaluating candidate evidence and building classification matrix..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Candidate Records & Engagement History:\n{context_str}\n\nOfficer Training Requirement:\n{req_context}"}
                            ],
                            temperature=0.1
                        )
                        st.session_state["last_comparison_text"] = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"Error calling LLM: {e}")

        if "last_comparison_text" in st.session_state:
            with st.container(border=True):
                st.markdown(st.session_state["last_comparison_text"])

st.markdown("---")
st.caption("Adult Educator Discovery & Comparison Assistant · AI Champions Bootcamp 2026")
