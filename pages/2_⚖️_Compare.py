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
st.caption("Evidence-Based Evaluation · Historical Engagement Records · Gap Analysis")
st.markdown("---")

# ── 2. Supabase Cloud Database Loaders ────────────────────────
@st.cache_data(ttl=600)
def load_trainer_profiles():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    response = supabase.table("AE_Mock_Dataset").select("*").execute()
    records = []
    for row in response.data:
        records.append({
            "Name": row.get("Full Name") or "Unknown",
            "Agency_or_Org": row.get("Organisation") or "Social Service Institute",
            "Designation": row.get("Designation") or "Adult Educator",
            "Sub_Sector": row.get("Sub-Sector") or "General",
            "Expertise": row.get("Domain Expertise") or "General Facilitation",
            "Qualifications": row.get("Highest Academic Qualifications") or "Degree",
            "Sector_Exp_Yrs": str(row.get("Years in Social Service Sector/Relevant Sector") or "N/A"),
            "Training_Exp_Yrs": str(row.get("Training Experience") or "N/A"),
            "ACTA_Certified": row.get("ACTA/ACLP Certified") or "Not documented",
            "Avg_Rating": str(row.get("Ave AE effectiveness in FY25") or "4.8")
        })
    return records

@st.cache_data(ttl=600)
def load_engagement_history():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    # Query all course runs from AE_Engagement table in Supabase
    response = supabase.table("AE_Engagement").select("*").execute()
    engagements = []
    for row in response.data:
        engagements.append({
            "Engagement_ID": row.get("Engagement ID") or "",
            "Sub_Sector": row.get("Sub-Sector") or "",
            "Course_Title": row.get("Course Title") or "",
            "Delivery_Mode": row.get("Mode of Delivery") or "",
            "AE_1": row.get("Fictional AE 1") or "",
            "AE_2": row.get("Fictional AE 2") or "",
            "AE_3": row.get("Fictional AE 3") or ""
        })
    return engagements

trainers = load_trainer_profiles()
engagements = load_engagement_history()
trainer_map = {t["Name"]: t for t in trainers}
all_names = [t["Name"] for t in trainers]

# Helper to find engagements for a trainer
def get_trainer_courses(trainer_name):
    matched_courses = []
    for eng in engagements:
        trainers_in_row = [eng["AE_1"], eng["AE_2"], eng["AE_3"]]
        if any(trainer_name.lower() in t.lower() for t in trainers_in_row if t):
            matched_courses.append({
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
            st.caption("No custom requirement carried from Discover page. You can still select candidates below to compare.")

with col_pick:
    default_selection = [name for name in shortlisted if name in all_names]
    selected_aes = st.multiselect(
        "Shortlisted Adult Educators:",
        options=all_names,
        default=default_selection
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
                st.markdown(f"### {ae_name}")
                if profile:
                    st.caption(f"{profile['Designation']} · {profile['Agency_or_Org']}")
                    st.markdown(f"**🏷️ Sub-Sector:** `{profile['Sub_Sector']}`")
                    
                    m1, m2 = st.columns(2)
                    with m1:
                        st.metric("Avg Rating", f"⭐ {profile['Avg_Rating']}/5.0")
                    with m2:
                        st.metric("Training Exp.", f"{profile['Training_Exp_Yrs']} yrs")
                    
                    st.markdown("---")
                    st.markdown(f"**🎯 Specialisation:**\n{profile['Expertise']}")
                    st.markdown(f"**🎓 Academic Qualifications:**\n{profile['Qualifications']}")
                    st.markdown(f"**📜 ACTA/ACLP:** {profile['ACTA_Certified']}")
                    st.markdown(f"**🏢 Sector Exp:** {profile['Sector_Exp_Yrs']} yrs")

                    st.markdown("---")
                    st.markdown(f"**📚 Documented Course Runs ({len(past_courses)} found):**")
                    if past_courses:
                        for c in past_courses[:3]:
                            st.markdown(f"- **{c['Course_Title']}**")
                            st.caption(f"  Sector: {c['Sub_Sector']} | Mode: {c['Delivery_Mode']}")
                    else:
                        st.caption("No specific course engagements found in current records.")
                else:
                    st.error("Profile not found.")

    # ── 5. AI Comparative Synthesis & Gap Analysis ───────────────
    st.markdown("---")
    st.subheader("3. AI Comparative Synthesis & Information Gaps")
    compare_btn = st.button("📊 Run AI Comparative Synthesis", type="primary", use_container_width=True)

    if compare_btn or "last_comparison_text" in st.session_state:
        if compare_btn:
            comparison_payload = []
            for name in selected_aes:
                p = trainer_map.get(name, {}).copy()
                p["Documented_Course_Runs"] = get_trainer_courses(name)[:5]
                comparison_payload.append(p)
                
            context_str = json.dumps(comparison_payload, indent=2)
            api_key = st.secrets.get("OPENAI_API_KEY", "")
            
            if not api_key:
                st.error("OpenAI API Key not found. Please verify `OPENAI_API_KEY` in Streamlit Cloud Settings → Secrets.")
            else:
                client = OpenAI(api_key=api_key)
                system_prompt = (
                    "You are an objective decision-support assistant for public social service training officers.\n"
                    "Your task is to compare the shortlisted Adult Educators side-by-side against the officer's training requirements.\n"
                    "Strict Grounding Rules:\n"
                    "1. Base all statements strictly on the provided records. Never invent background, experience, or ratings.\n"
                    "2. Evaluate how each candidate aligns with the requirements.\n"
                    "3. Highlight key trade-offs between the candidates (e.g., academic qualifications vs. frontline experience vs. past course engagements taught).\n"
                    "4. Identify any information gaps: explicitly state 'Not documented in available records' for any criteria not found in the profiles.\n"
                    "5. Maintain a neutral decision-support tone: Never declare a 'winner', 'best candidate', or 'recommended choice'. Remind the officer that final engagement discretion rests with them."
                )

                with st.spinner("Synthesizing comparative evidence and evaluating trade-offs..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Candidate Records & Engagement History:\n{context_str}\n\nOfficer Requirement:\n{officer_requirement}"}
                            ],
                            temperature=0.2
                        )
                        st.session_state["last_comparison_text"] = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"Error calling LLM: {e}")

        if "last_comparison_text" in st.session_state:
            with st.container(border=True):
                st.markdown(st.session_state["last_comparison_text"])

st.markdown("---")
st.caption("Adult Educator Discovery & Comparison Assistant · AI Champions Bootcamp 2026")
