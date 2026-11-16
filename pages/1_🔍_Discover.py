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

# ── 2. Cloud Database Loader (Supabase External Storage) ────────
@st.cache_data(ttl=600)
def load_all_ae_records():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    # Query all 100 Adult Educator records from Supabase
    response = supabase.table("AE_Mock_Dataset").select("*").execute()
    records = []
    
    for idx, row in enumerate(response.data, start=1):
        name_val = get_col(row, ["Full Name", "Name", "Trainer Name", "AE Name"], "Unknown")
        org_val = get_col(row, ["Organisation", "Organization", "Agency", "Agency_or_Org"], "Social Service Institute")
        desig_val = get_col(row, ["Designation", "Role", "Title"], "Adult Educator")
        subsector_val = get_col(row, ["Sub-Sector", "Sub_Sector", "Sub Sector", "Subsector", "Sector"], "Social Service")
        exp_val = get_col(row, ["Domain Expertise", "Area of Specialisation / Core Expertise", "Expertise", "Specialisation"], "General Facilitation")
        qual_val = get_col(row, ["Highest Academic Qualifications", "Qualifications", "Academic Qualifications"], "Professional Degree")
        sec_yrs = get_col(row, ["Years in Social Service Sector/Relevant Sector", "Sector_Exp_Yrs", "Sector Experience"], "10")
        trn_yrs = get_col(row, ["Training Experience", "Training_Exp_Yrs", "Years of Training Experience"], "5")
        acta_val = get_col(row, ["ACTA/ACLP Certified", "ACTA_Certified", "ACTA/ACLP"], "Yes")
        runs_fy25 = get_col(row, ["No of runs in FY25", "FY25_Runs", "No. of runs in FY25"], "Not documented")
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
            "FY25_Course_Runs": str(runs_fy25),
            "Avg_Rating": str(rating_val)
        })
    return records

try:
    ae_records = load_all_ae_records()
except Exception as e:
    st.error(f"Error connecting to Supabase database: {e}")
    ae_records = []

candidate_options = [r["Name"] for r in ae_records]
ae_lookup = {r["Name"]: r for r in ae_records}

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
        placeholder="e.g., Looking for an Adult Educator who has experience working with persons with disabilities and special needs for the past 5 years."
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
        st.session_state["match_status"] = ""
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
        st.caption("Live PostgreSQL records fetched via Supabase API (AE_Mock_Dataset · FY25 Profile Metrics).")

# ── 4. Retrieval & Analysis Execution ─────────────────────────
if find_clicked:
    if not user_requirement.strip():
        st.warning("⚠️ Please enter a training requirement before searching.")
    else:
        st.session_state["last_requirement"] = user_requirement
        
        # Prepare all concise profiles with explicit Record_IDs and FY25 run metrics for the LLM
        compact_profiles = [
            {
                "Record_ID": r["Record_ID"],
                "Source_Reference": f"{r['Record_ID']} | {r['Source_Table']}",
                "Name": r["Name"],
                "Designation": r["Designation"],
                "Organisation": r["Agency_or_Org"],
                "Sub_Sector": r["Sub_Sector"],
                "Domain_Expertise": r["Expertise"],
                "Qualifications": r["Qualifications"],
                "Sector_Exp_Yrs": r["Sector_Exp_Yrs"],
                "Training_Exp_Yrs": r["Training_Exp_Yrs"],
                "ACTA_Certified": r["ACTA_Certified"],
                "FY25_Course_Runs": r["FY25_Course_Runs"],
                "FY25_Avg_Rating": r["Avg_Rating"]
            }
            for r in ae_records
        ]
        context_str = json.dumps(compact_profiles, indent=1)
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        
        if not api_key:
            st.error("OpenAI API Key not found. Please configure OPENAI_API_KEY in Streamlit Cloud Settings → Secrets.")
        else:
            client = OpenAI(api_key=api_key)
            
            system_prompt = (
                "You are the Adult Educator (AE) Discovery Assistant for public social service training officers.\n"
                "Your role is decision support ONLY. You MUST strictly separate Domain Classification from Evidence Matching using this 3-Step Workflow:\n\n"
                "DATASET SCHEMA & TEMPORAL BOUNDARY NOTICE:\n"
                "- The AE profile database (`AE_Mock_Dataset`) records `FY25_Course_Runs` (number of runs in FY25, ranging from ~4 to 16 runs) and `FY25_Avg_Rating`. It does NOT contain complete FY2026 training-run totals.\n"
                "- Before making any definitive claim about 2026 training runs, phd/doctoral degrees, or specific credentials, check whether the dataset actually documents that field.\n\n"
                "STEP 1 — IS THE TRAINING DOMAIN RELEVANT TO SOCIAL SERVICES?\n"
                "- Core Social Service Domains in Scope: Disability & Special Needs, Children & Youth, Family, Mental Health & Caregiving (including eldercare, dementia, palliative care, bereavement), Volunteer Management, Foster Parents, Social Service Leadership, and Professional Practice/Ethics (MOD).\n"
                "- IF OUT OF SCOPE (strictly non-social-service technical, industrial, or corporate fields like Civil Engineering, Aviation Flight Dynamics, Crypto Trading, Commercial Real Estate):\n"
                "  1. Start your response with the exact tag: `STATUS: NO_RELEVANT_DOMAIN`\n"
                "  2. State clearly that the requested domain is outside the social service training scope.\n"
                "  3. Do NOT name or recommend any candidates.\n"
                "- IF IN SCOPE: Proceed to Step 2.\n\n"
                "STEP 2 — CHECK EVERY MANDATORY REQUIREMENT IN THE QUERY\n"
                "- Break down all mandatory conditions stated by the officer (e.g., specific domain/population experience, specific academic qualification such as PhD/Master's, minimum years of training/sector experience, or minimum number of SSI training runs in a specific year like 2026).\n"
                "- Check the 100 AE records to see if any candidates simultaneously satisfy ALL stated mandatory requirements.\n\n"
                "STEP 3 — RETURN VERIFIED MATCHES, PARTIAL MATCHES, OR INSUFFICIENT EVIDENCE\n"
                "Case A — One or more AEs meet the core requirements (`STATUS: VERIFIED_MATCH`):\n"
                "- Start your response with the exact tag: `STATUS: VERIFIED_MATCH`\n"
                "- Present the top 2 to 3 matching Adult Educators using the candidate format below.\n\n"
                "Case B — Domain is relevant to social services, but NO candidate simultaneously meets all mandatory requirements (`STATUS: PARTIAL_MATCH`):\n"
                "- Start your response with the exact tag: `STATUS: PARTIAL_MATCH`\n"
                "- Immediately output this structured notice at the top:\n"
                "  **⚠️ No Adult Educators were verified as meeting all specified requirements based on the available records.**\n"
                "  The requested expertise is relevant to social services. However, the available records do not establish a candidate who simultaneously meets [list the exact combination of requirements, e.g., the required youth experience, PhD qualification, and minimum 20 SSI training runs in 2026].\n"
                "  *Dataset Note:* Please note that `AE_Mock_Dataset` only documents FY25 training run counts (`FY25_Course_Runs`) and does not contain complete FY2026 training-run totals.\n"
                "  You may revise the criteria or review the partially matching profiles below. Any missing information should be verified separately.\n"
                "- Below that notice, add the heading `### Partially Matching Profiles (For Optional Review)` and list the 2 to 3 closest domain candidates using the candidate format below, clearly detailing which requirements are met and which are unmet under `Information Gaps`.\n\n"
                "CANDIDATE OUTPUT FORMAT (Use for both Verified Matches and Partially Matching Profiles):\n"
                "Candidate X: [Exact Full Name] ([Record_ID])\n"
                "- **Candidate Name, Designation & Organisation**: [Exact Full Name], [Designation] ([Organisation])\n"
                "- **Source Record Reference**: [Insert exact Source_Reference string, e.g., AE-001 | Supabase: AE_Mock_Dataset (Row 1)]\n"
                "- **Sub-Sector & Documented Expertise Field**: Sub-Sector: [Sub_Sector] | Domain Expertise: \"[Exact Domain_Expertise string]\" | Qualifications: [Qualifications]\n"
                "- **Documented Match Rationale**: [Explain which requirements are supported by the record and which are only partially met]\n"
                "- **Experience, FY25 Runs & Effectiveness Rating**: [Training_Exp_Yrs] yrs training exp ([Sector_Exp_Yrs] yrs sector exp) | FY25 Runs: [FY25_Course_Runs] | FY25 Rating: [FY25_Avg_Rating]/5.0 | ACTA/ACLP: [ACTA_Certified]\n"
                "- **Information Gaps**: [Explicitly list any unmet requirements or dataset limitations, e.g., 'PhD qualification not documented (holds Master of Social Work); complete FY2026 training runs not documented in available records (FY25 runs: 9)']\n\n"
                "RULE ON NEUTRAL DECISION SUPPORT:\n"
                "- Never declare any candidate as 'the best' or 'winner'."
            )

            with st.spinner("Checking domain relevance and verifying mandatory requirements against AE records..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"All AE Records:\n{context_str}\n\nOfficer Training Requirement:\n{user_requirement}"}
                        ],
                        temperature=0.1
                    )
                    analysis_text = response.choices[0].message.content
                    
                    # Determine routing status
                    if "STATUS: NO_RELEVANT_DOMAIN" in analysis_text:
                        match_status = "NO_RELEVANT_DOMAIN"
                    elif "STATUS: PARTIAL_MATCH" in analysis_text:
                        match_status = "PARTIAL_MATCH"
                    else:
                        match_status = "VERIFIED_MATCH"
                        
                    st.session_state["match_status"] = match_status
                    
                    # Clean status tags from display text
                    clean_text = (
                        analysis_text
                        .replace("STATUS: NO_RELEVANT_DOMAIN", "")
                        .replace("STATUS: PARTIAL_MATCH", "")
                        .replace("STATUS: VERIFIED_MATCH", "")
                        .lstrip(". \n")
                        .strip()
                    )
                    st.session_state["discovery_analysis"] = clean_text
                    
                    # ── Candidate Name Detection ───────────────────────────
                    extracted_names = []
                    if match_status != "NO_RELEVANT_DOMAIN":
                        found_candidates = []
                        for real_name in candidate_options:
                            pos = clean_text.find(real_name)
                            if pos != -1:
                                found_candidates.append((pos, real_name))
                        
                        found_candidates.sort(key=lambda x: x[0])
                        for _, name in found_candidates:
                            if name not in extracted_names:
                                extracted_names.append(name)
                    
                    top_matches = extracted_names[:3]
                    st.session_state["ai_suggested_candidates"] = top_matches
                    
                    if top_matches:
                        st.session_state["selected_candidates"] = top_matches
                        st.session_state["discover_picker"] = top_matches
                        if "compare_picker" in st.session_state:
                            st.session_state["compare_picker"] = top_matches
                    else:
                        st.session_state["selected_candidates"] = []
                        st.session_state["discover_picker"] = []
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"Error calling LLM: {e}")

# ── 5. Render Discovery Results (If Search Run) ───────────────
if "discovery_analysis" in st.session_state:
    st.markdown("---")
    st.subheader("2. AI Discovery Analysis & Evidence")
    
    match_status = st.session_state.get("match_status", "VERIFIED_MATCH")
    ai_suggestions = st.session_state.get("ai_suggested_candidates", [])
    
    if match_status == "NO_RELEVANT_DOMAIN" or not ai_suggestions:
        st.warning(
            "⚠️ **Out of Scope / No Relevant Domain Found:** "
            "The requested training domain falls outside the social service records in this database."
        )
    elif match_status == "PARTIAL_MATCH":
        st.warning(
            "🟡 **Partial Match / Insufficient Evidence for All Mandatory Criteria:** "
            "No Adult Educators were verified as meeting all specified requirements simultaneously. "
            "Review the gap notice and partially matching profiles below."
        )
    else:
        st.success(
            "🟢 **Verified Domain & Evidence Match:** "
            "Adult Educators matching your stated training requirements were identified in the records."
        )

    with st.container(border=True):
        st.markdown(st.session_state["discovery_analysis"])
        
    if ai_suggestions:
        # ── Direct Source Record Verification Panel (Fixes UAT-005) ──
        with st.expander("📄 View Underlying Source Records for Surfaced Candidates (Traceability Verification)", expanded=True):
            st.caption("Direct database extract from Supabase (AE_Mock_Dataset) supporting the AI analysis above:")
            ev_cols = st.columns(len(ai_suggestions))
            for idx, c_name in enumerate(ai_suggestions):
                rec = ae_lookup.get(c_name)
                if rec:
                    with ev_cols[idx]:
                        with st.container(border=True):
                            st.markdown(f"**{rec['Record_ID']} · {rec['Name']}**")
                            st.caption(f"Source: {rec['Source_Table']}")
                            st.markdown(f"- **Designation:** {rec['Designation']} ({rec['Agency_or_Org']})")
                            st.markdown(f"- **Sub-Sector Field:** {rec['Sub_Sector']}")
                            st.markdown(f"- **Domain Expertise Field:** *{rec['Expertise']}*")
                            st.markdown(f"- **Qualifications:** {rec['Qualifications']}")
                            st.markdown(f"- **Sector / Training Exp:** {rec['Sector_Exp_Yrs']} yrs / {rec['Training_Exp_Yrs']} yrs")
                            st.markdown(f"- **FY25 Runs:** {rec['FY25_Course_Runs']} runs *(FY2026 totals not in profile table)*")
                            st.markdown(f"- **ACTA/ACLP:** {rec['ACTA_Certified']} | **Rating:** ⭐ {rec['Avg_Rating']}/5.0")

        # Prompt user to confirm or proceed
        st.markdown("---")
        with st.container(border=True):
            if match_status == "PARTIAL_MATCH":
                st.markdown("#### 🎯 Partially Matching Candidates (Optional Comparison)")
                st.caption("Although no candidate met all mandatory criteria simultaneously, these partially matching profiles have been pre-selected if you wish to compare their trade-offs and gaps side-by-side.")
            else:
                st.markdown("#### 🎯 Shortlisted Candidates for Comparison")
            st.write(f"Pre-selected: **{', '.join(ai_suggestions)}**")
            
            c_yes, c_no, _ = st.columns([1, 1, 2])
            with c_yes:
                if st.button("✅ Proceed to Compare Page", type="primary", use_container_width=True):
                    st.session_state["selected_candidates"] = ai_suggestions
                    st.session_state["discover_picker"] = ai_suggestions
                    if "compare_picker" in st.session_state:
                        st.session_state["compare_picker"] = ai_suggestions
                    st.switch_page("pages/2_⚖️_Compare.py")
            with c_no:
                if st.button("❌ Clear & Revise Search", use_container_width=True):
                    st.session_state["last_requirement"] = ""
                    st.session_state["selected_candidates"] = []
                    st.session_state["discover_picker"] = []
                    st.session_state["ai_suggested_candidates"] = []
                    st.session_state["match_status"] = ""
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

current_selected = [
    name for name in st.session_state.get("selected_candidates", []) if name in candidate_options
]

def sync_discover_candidates():
    st.session_state["selected_candidates"] = st.session_state["discover_picker"]

selected_aes = st.multiselect(
    "Select at least 2 Adult Educators to compare side-by-side:",
    options=candidate_options,
    default=current_selected,
    key="discover_picker",
    on_change=sync_discover_candidates,
    placeholder="Choose Adult Educators from recommendations or directory..."
)
st.session_state["selected_candidates"] = selected_aes

if len(selected_aes) >= 2:
    st.success(f"✅ **{len(selected_aes)} candidates shortlisted ({', '.join(selected_aes)})!** You can now proceed to the **2 ⚖️ Compare** page in the left sidebar.")
else:
    st.info("ℹ️ Select at least 2 candidates to enable full comparative analysis.")

# ── 7. Enhanced Profile Explorer (Natural Cards) ──────────────
st.markdown("---")
with st.expander("👤 Browse Adult Educator Profiles Directory", expanded=False):
    st.caption("Search or preview trainer credentials from the synthetic knowledge base.")
    
    search_filter = st.text_input("Filter profiles by name, Record ID, or keyword:", placeholder="e.g. AE-001, Disability, Youth, Trauma...")
    
    displayed_records = ae_records
    if search_filter:
        displayed_records = [
            r for r in ae_records
            if search_filter.lower() in r["Name"].lower()
            or search_filter.lower() in r["Record_ID"].lower()
            or search_filter.lower() in r["Expertise"].lower()
            or search_filter.lower() in r["Sub_Sector"].lower()
        ]

    for profile in displayed_records[:8]:
        with st.container(border=True):
            col_main, col_stats = st.columns([3, 1])
            with col_main:
                st.markdown(f"### {profile['Record_ID']} · {profile['Name']}")
                st.markdown(f"**{profile['Designation']}** · *{profile['Agency_or_Org']}*")
                st.markdown(f"**🏷️ Sub-Sector:** {profile['Sub_Sector']}")
                st.markdown(f"**🎯 Specialisation / Expertise:** {profile['Expertise']}")
                st.caption(f"🎓 Qualifications: {profile['Qualifications']} | ACTA/ACLP: {profile['ACTA_Certified']} | FY25 Runs: {profile['FY25_Course_Runs']} | Source: {profile['Source_Table']}")
            with col_stats:
                st.metric("Avg Effectiveness", f"⭐ {profile['Avg_Rating']}/5.0")
                st.metric("Training Exp.", f"{profile['Training_Exp_Yrs']} yrs")
