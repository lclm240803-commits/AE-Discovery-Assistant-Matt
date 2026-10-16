import streamlit as st
import json
import os
import zipfile
import xml.etree.ElementTree as ET
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
st.caption("AI-Assisted Capability Matching · Decision Support for Training Officers")
st.markdown("---")

# ── 2. Native Robust Data Loader (AppLocker-Compliant) ────────
@st.cache_data
def load_all_ae_records():
    excel_path = "SSI_AE_Mock_Dataset_100_Trainers.xlsx"
    records = []

    if os.path.exists(excel_path):
        try:
            with zipfile.ZipFile(excel_path, 'r') as z:
                shared_strings = []
                if 'xl/sharedStrings.xml' in z.namelist():
                    tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                    for elem in tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                        parts = [t.text for t in elem.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text]
                        shared_strings.append("".join(parts))

                sheet_tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
                rows = sheet_tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                
                if len(rows) >= 4:
                    for r in rows[3:]:
                        cells = []
                        for c in r.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                            v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            if v is not None:
                                val = v.text
                                if c.attrib.get('t') == 's' and shared_strings:
                                    cells.append(shared_strings[int(val)])
                                else:
                                    cells.append(val)
                            else:
                                is_elem = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}is/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                                if is_elem is not None and is_elem.text:
                                    cells.append(is_elem.text)
                                else:
                                    cells.append("")

                        if cells and len(cells) >= 11:
                            rec = {
                                "Name": cells[0] if len(cells) > 0 else "Unknown",
                                "Agency_or_Org": cells[7] if len(cells) > 7 else "Social Service Institute",
                                "Designation": cells[8] if len(cells) > 8 else "Adult Educator",
                                "Sub_Sector": cells[9] if len(cells) > 9 else "General",
                                "Expertise": cells[10] if len(cells) > 10 else "General Facilitation",
                                "Qualifications": cells[11] if len(cells) > 11 else "Professional Degree",
                                "Training_Exp_Yrs": cells[16] if len(cells) > 16 else "5",
                                "ACTA_Certified": cells[21] if len(cells) > 21 else "Yes",
                                "Avg_Rating": cells[27] if len(cells) > 27 else "4.8"
                            }
                            records.append(rec)
        except Exception:
            pass

    return records

ae_records = load_all_ae_records()
candidate_options = [r["Name"] for r in ae_records]

# Ensure session state key exists
if "selected_candidates" not in st.session_state:
    st.session_state["selected_candidates"] = []

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
    find_clicked = st.button("🔎 Search Relevant Adult Educators", type="primary", use_container_width=True)

with col_info:
    with st.container(border=True):
        st.markdown("**Dataset Overview**")
        st.metric("Total AE Profiles", len(ae_records))
        st.caption("Matches natural-language needs against verified competency records.")

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
                "Your role is decision support ONLY. Follow these strict rules:\n"
                "1. Base all statements strictly on the provided AE records. Do NOT invent credentials, experience, or ratings.\n"
                "2. Identify the 2 to 3 most relevant AEs matching the requirement.\n"
                "3. If NO candidates match the requirements in the provided records, do NOT recommend or invent any candidates. Under 'Candidate Name & Designation' explicitly write 'Not documented in available records', and clearly state in 'Information Gaps' that no matching candidates exist.\n"
                "4. For each candidate, format strictly as:\n"
                "   Candidate X\n"
                "   - **Candidate Name & Designation**: [Exact Full Name], [Designation]\n"
                "   - **Sub-Sector Alignment**: [Alignment]\n"
                "   - **Documented Match Rationale**: [Reasoning]\n"
                "   - **Years of Training Experience & Historical Effectiveness Rating**: [Exp], [Rating]\n"
                "   - **Information Gaps**: [Gaps or 'Not documented in available records']\n"
                "5. Maintain a neutral decision-support tone: Never label any candidate as 'the best' or 'winner'."
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
                    
                    # Intelligently extract names that appear in candidate_options
                    extracted_names = []
                    for name in candidate_options:
                        if name in analysis_text and name not in extracted_names:
                            extracted_names.append(name)
                    
                    # Directly update the session state key bound to the multiselect widget
                    if extracted_names:
                        st.session_state["selected_candidates"] = extracted_names[:3]
                    else:
                        st.session_state["selected_candidates"] = []

                except Exception as e:
                    st.error(f"Error calling LLM: {e}")

# ── 5. Render Discovery Results (If Search Run) ───────────────
if "discovery_analysis" in st.session_state:
    st.markdown("---")
    st.subheader("2. AI Discovery Analysis & Evidence")
    
    with st.container(border=True):
        st.markdown(st.session_state["discovery_analysis"])
        
    current_shortlist = st.session_state.get("selected_candidates", [])
    if not current_shortlist:
        st.warning("⚠️ **No matching Adult Educators found in the records for these criteria.** Try adjusting your requirements (e.g., searching for *Children & Youth*, *Family*, *Disability*, or *Mental Health*), or manually pick candidates below.")

# ── 6. Candidate Shortlisting for Compare Page (Always Visible) ─
st.markdown("---")
st.subheader("3. Shortlist Candidates for Comparison")
st.caption("Selected candidates will be carried over to the **2 ⚖️ Compare** page.")

# Using key="selected_candidates" directly ensures Streamlit manages selection state
# without dropping items on re-runs.
selected_aes = st.multiselect(
    "Select at least 2 Adult Educators to compare side-by-side:",
    options=candidate_options,
    key="selected_candidates",
    placeholder="Choose Adult Educators from recommendations or directory..."
)

if len(selected_aes) >= 2:
    st.success(f"✅ **{len(selected_aes)} candidates shortlisted!** You can now proceed to the **2 ⚖️ Compare** page in the left sidebar.")
else:
    st.info("ℹ️ Select at least 2 candidates to enable full comparative analysis.")

# ── 7. Enhanced Profile Explorer (Natural Cards) ──────────────
st.markdown("---")
with st.expander("👤 Browse Adult Educator Profiles Directory", expanded=False):
    st.caption("Search or preview trainer credentials from the synthetic knowledge base.")
    
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