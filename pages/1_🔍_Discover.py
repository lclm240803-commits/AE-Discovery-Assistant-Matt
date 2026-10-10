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
st.markdown(
    """
    Identify potential **Adult Educators (AEs)** by describing your course or engagement requirements 
    in natural language. The system grounds all recommendations strictly in documented synthetic records.
    """
)
st.markdown("---")

# ── 2. Native Robust Data Loader (Bypasses DLL/AppLocker issues) ─
@st.cache_data
def load_all_ae_records():
    excel_path = "SSI_AE_Mock_Dataset_100_Trainers.xlsx"
    records = []

    if os.path.exists(excel_path):
        try:
            with zipfile.ZipFile(excel_path, 'r') as z:
                # Read shared strings table
                shared_strings = []
                if 'xl/sharedStrings.xml' in z.namelist():
                    tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                    for elem in tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                        parts = [t.text for t in elem.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text]
                        shared_strings.append("".join(parts))

                # Read 'sheet1.xml' (AE Mock Data)
                sheet_tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
                rows = sheet_tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                
                # Headers are on Row 3
                headers = []
                if len(rows) >= 3:
                    for c in rows[2].findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                        v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        if v is not None:
                            val = v.text
                            if c.attrib.get('t') == 's' and shared_strings:
                                headers.append(shared_strings[int(val)])
                            else:
                                headers.append(val)

                    # Data rows start from Row 4 onwards
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
                                "Agency_or_Org": cells[7] if len(cells) > 7 else "",
                                "Designation": cells[8] if len(cells) > 8 else "",
                                "Sub_Sector": cells[9] if len(cells) > 9 else "",
                                "Expertise": cells[10] if len(cells) > 10 else "",
                                "Qualifications": cells[11] if len(cells) > 11 else "",
                                "Training_Exp_Yrs": cells[16] if len(cells) > 16 else "",
                                "ACTA_Certified": cells[21] if len(cells) > 21 else "",
                                "Avg_Rating": cells[27] if len(cells) > 27 else "4.5"
                            }
                            records.append(rec)
        except Exception:
            pass

    # Fallback if file is absent
    if not records:
        records = [
            {
                "Name": "Tan Wei Ming",
                "Sub_Sector": "Children & Youth",
                "Expertise": "Youth-at-risk; trauma-informed practice; family work",
                "Qualifications": "Master of Social Work",
                "Training_Exp_Yrs": "11",
                "Avg_Rating": "4.9"
            },
            {
                "Name": "Nur Aisyah Rahman",
                "Sub_Sector": "Family",
                "Expertise": "Family strengthening; parenting; caregiver engagement; motivational interviewing",
                "Qualifications": "Master of Counselling",
                "Training_Exp_Yrs": "14",
                "Avg_Rating": "4.8"
            }
        ]
    return records

ae_records = load_all_ae_records()

# ── 3. Search Interface ───────────────────────────────────────
col_query, col_filters = st.columns([3, 1])

with col_query:
    default_prompt = st.session_state.get("last_requirement", "")
    user_requirement = st.text_area(
        "Enter Engagement / Training Requirements (Natural Language):",
        value=default_prompt,
        height=140,
        placeholder="e.g., Looking for an Adult Educator with strong experience in trauma-informed intervention and casework with youth-at-risk."
    )

with col_filters:
    st.subheader("Dataset Scope")
    st.info(f"📚 **{len(ae_records)}** AE Profiles Loaded")
    st.caption("Matches natural-language needs against documented sector skills.")

find_clicked = st.button("🔎 Find Potentially Relevant AEs", type="primary")

# ── 4. Retrieval & Analysis Execution ─────────────────────────
if find_clicked:
    if not user_requirement.strip():
        st.warning("⚠️ Please provide training requirements before searching.")
    else:
        st.session_state["last_requirement"] = user_requirement
        
        # Format the top records into context
        context_str = json.dumps(ae_records[:30], indent=2)

        # Retrieve OpenAI API Key from Streamlit Secrets
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        
        if not api_key:
            st.error("OpenAI API Key not found in Streamlit Secrets. Please configure `OPENAI_API_KEY` in Settings.")
        else:
            client = OpenAI(api_key=api_key)
            
            system_prompt = (
                "You are the Adult Educator (AE) Discovery Assistant for public social service training officers.\n"
                "Your role is decision support ONLY. Follow these strict rules:\n"
                "1. Base all statements strictly on the provided AE records. Do NOT invent credentials, experience, or ratings.\n"
                "2. Identify the 2 to 3 most relevant AEs matching the requirement.\n"
                "3. For each candidate, provide:\n"
                "   - **AE Name**\n"
                "   - **Sub-Sector & Documented Expertise**\n"
                "   - **Documented Match Rationale**: Why their profile aligns with the requirement.\n"
                "   - **Training Experience & Historical Rating**\n"
                "   - **Information Gaps**: Explicitly state 'Not documented in available records' for any criteria not found in the profile.\n"
                "4. Maintain a neutral decision-support tone: Never label any candidate as 'the best', 'winner', or 'selected'. Final choice belongs to the officer."
            )

            with st.spinner("Analyzing AE profiles against requirement..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"AE Records:\n{context_str}\n\nOfficer Requirement:\n{user_requirement}"}
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
    
    candidate_options = [r["Name"] for r in ae_records]
    
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

with st.expander("📂 View Sample Raw AE Records"):
    st.write(ae_records[:10])