import streamlit as st
import json
import os
import tempfile
import asyncio
import sys

# Ensure project root is in sys.path so agents can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import run_pipeline, run_strategist

# Set page config
st.set_page_config(page_title=" RFP Bid/No-Bid Triage Agent", page_icon="📄")

# --- SIDEBAR ---
profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'company_profile.json')
if os.path.exists(profile_path):
    with open(profile_path, 'r', encoding='utf-8') as f:
        company_profile = json.load(f)
    
    st.sidebar.title("Our Company Profile")
    st.sidebar.subheader(company_profile.get("name", "Company"))
    
    st.sidebar.markdown("**Certifications:**")
    for k, v in company_profile.get("security_certifications", {}).items():
        st.sidebar.markdown(f"- {k} ({v})")
        
    st.sidebar.markdown("**Domains:**")
    for domain in company_profile.get("domains_of_expertise", []):
        st.sidebar.markdown(f"- {domain}")
        
    st.sidebar.markdown("**Cloud Infrastructure:**")
    for k, v in company_profile.get("cloud_infrastructure", {}).items():
        st.sidebar.markdown(f"- {k}: {v}")

# --- MAIN AREA ---
st.title(" RFP Bid/No-Bid Triage Agent")

# Initialize session state variables
if "pipeline_result" not in st.session_state:
    st.session_state["pipeline_result"] = None
if "hitl_decisions" not in st.session_state:
    st.session_state["hitl_decisions"] = {}
if "strategist_result" not in st.session_state:
    st.session_state["strategist_result"] = None
if "processed_file_id" not in st.session_state:
    st.session_state["processed_file_id"] = None

uploaded_file = st.file_uploader("Upload RFP Document", type=["pdf"])

if uploaded_file is not None:
    # Check if this is a new file
    file_id = uploaded_file.file_id
    if file_id != st.session_state["processed_file_id"]:
        # Reset state for new file
        st.session_state["pipeline_result"] = None
        st.session_state["hitl_decisions"] = {}
        st.session_state["strategist_result"] = None
        st.session_state["processed_file_id"] = file_id
        
    if st.session_state["pipeline_result"] is None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = tmp.name
            
        with st.spinner(" Agent 1/3: Extracting requirements from RFP..."):
            result = asyncio.run(run_pipeline(pdf_path))
            st.session_state["pipeline_result"] = result
            
        # Clean up temp file
        os.unlink(pdf_path)

    res = st.session_state["pipeline_result"]
    if res:
        ext_res = res.get("extraction", {})
        
        # PHASE 1 Check
        if ext_res.get("status") == "SECURITY_ALERT":
            st.error(" SECURITY ALERT: Prompt injection attempt detected in this document. Pipeline halted for your protection.")
            st.code(ext_res.get("triggered_phrase", ""))
            st.markdown(
                """
                <div style="background-color:red;padding:10px;border-radius:5px;color:white;text-align:center;">
                <strong>SECURITY HALT ACTIVE</strong>
                </div>
                """, unsafe_allow_html=True
            )
            st.stop()
            
        # Success Extraction
        reqs = ext_res.get("requirements", [])
        st.success(f" Extraction complete  {len(reqs)} requirements found")
        
        # PHASE 2: Critic Validation
        crit_res = res.get("critic", {})
        validated = crit_res.get("validated", [])
        flagged = crit_res.get("flagged", [])
        
        st.markdown("### Agent 2/3: Validating requirements for hallucinations...")
        col1, col2 = st.columns(2)
        col1.metric("Validated ", len(validated))
        col2.metric("Flagged ", len(flagged))
        
        # PHASE 3: HITL Triage
        proceed_to_strategist = False
        
        if len(flagged) > 0:
            st.warning(" Human Review Required Before Final Decision")
            reviewed_count = len(st.session_state["hitl_decisions"])
            
            with st.expander(f"Review Flagged Requirements ({len(flagged)} items)", expanded=True):
                for item in flagged:
                    item_id = item.get("id")
                    st.markdown(f"**{item.get('description')}**")
                    st.markdown(f"*{item.get('reason')}*")
                    
                    if item_id in st.session_state["hitl_decisions"]:
                        dec = st.session_state["hitl_decisions"][item_id]
                        if dec == "KEEP":
                            st.info("Decision:  Force Keep")
                        else:
                            st.info("Decision:  Discard")
                    else:
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            if st.button(" Force Keep", key=f"keep_{item_id}"):
                                st.session_state["hitl_decisions"][item_id] = "KEEP"
                                st.rerun()
                        with bc2:
                            if st.button(" Discard", key=f"discard_{item_id}"):
                                st.session_state["hitl_decisions"][item_id] = "DISCARD"
                                st.rerun()
                    st.divider()
                    
            st.write(f"*{reviewed_count} of {len(flagged)} items reviewed*")
            
            if reviewed_count == len(flagged):
                if st.button(" Proceed to Final Decision"):
                    proceed_to_strategist = True
        else:
            proceed_to_strategist = True
            
        # PHASE 4: Strategist Decision
        # Run if ready and hasn't been run yet
        if proceed_to_strategist and st.session_state["strategist_result"] is None:
            with st.spinner(" Agent 3/3: Consulting company capabilities and making decision..."):
                hitl_resolved_items = []
                for item in flagged:
                    if st.session_state["hitl_decisions"].get(item.get("id")) == "KEEP":
                        hitl_resolved_items.append(item)
                        
                strat_res = asyncio.run(run_strategist(validated, hitl_resolved_items))
                st.session_state["strategist_result"] = strat_res
                
        # DISPLAY THE DECISION
        strat_res = st.session_state["strategist_result"]
        if strat_res:
            decision = strat_res.get("decision", "")
            if decision.upper() == "BID":
                st.markdown("<h1 style='color:green;'> RECOMMENDATION: BID</h1>", unsafe_allow_html=True)
            elif decision.upper() == "NO-BID":
                st.markdown("<h1 style='color:red;'> RECOMMENDATION: NO-BID</h1>", unsafe_allow_html=True)
                
            conf = strat_res.get("confidence_score", 0)
            conf_val = min(max(conf / 100.0, 0.0), 1.0)
            st.progress(conf_val, text=f"Confidence: {conf}%")
            
            dealbreakers = strat_res.get("dealbreakers_found", [])
            if dealbreakers:
                st.error("Dealbreakers:\n" + "\n".join([f"- {d}" for d in dealbreakers]))
                
            risks = strat_res.get("risks", [])
            if risks:
                st.warning("Risks:\n" + "\n".join([f"- {r}" for r in risks]))
                
            with st.expander(" Full Reasoning", expanded=False):
                st.write(strat_res.get("reasoning", ""))
                
            with st.expander(" Requirement Match Details"):
                matches = strat_res.get("strong_matches", [])
                for m in matches:
                    st.markdown(f"<span style='color:green;'>- {m}</span>", unsafe_allow_html=True)
                    
            if st.button(" Analyse New RFP"):
                st.session_state["pipeline_result"] = None
                st.session_state["hitl_decisions"] = {}
                st.session_state["strategist_result"] = None
                st.session_state["processed_file_id"] = None
                st.rerun()
