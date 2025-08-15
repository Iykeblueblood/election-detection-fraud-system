# app.py
import streamlit as st
import pandas as pd
import joblib
from rules_engine import RULES, evaluate_rules
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="Election Fraud Detection System", layout="wide", page_icon="警")

# --- Load Model ---
try:
    model = joblib.load('fraud_model.joblib')
except FileNotFoundError:
    st.error("Model not found. Please run `train_fraud_model.py` first.")
    st.stop()

# --- Sidebar Inputs ---
with st.sidebar:
    st.title("Polling Unit Data Input")
    st.markdown("Enter the data from a polling unit's result sheet (Form EC8A) to analyze it for potential fraud indicators.")
    
    st.header("Voter & Ballot Numbers")
    registered_voters = st.number_input("Registered Voters", 0, 2000, 550)
    accredited_voters = st.number_input("Accredited Voters", 0, 2000, 310)
    votes_cast = st.number_input("Total Votes Cast", 0, 2000, 305)
    valid_votes = st.number_input("Total Valid Votes", 0, 2000, 300)
    
    st.header("Party Vote Counts")
    pdp_votes = st.number_input("PDP Votes", 0, 2000, 150)
    apc_votes = st.number_input("APC Votes", 0, 2000, 100)
    lp_votes = st.number_input("LP Votes", 0, 2000, 45)
    other_votes = st.number_input("Other Parties Votes", 0, 2000, 5)

    st.header("Procedural & Contextual Data")
    submission_delay_hours = st.slider("Result Submission Delay (Hours)", 0.0, 12.0, 1.5, 0.5)
    form_ec8a_missing_or_altered = st.checkbox("Form EC8A Missing or Visibly Altered")
    reports_of_violence = st.checkbox("Reports of Violence or Intimidation")
    bvas_malfunction = st.checkbox("BVAS Reported Malfunctioning")
    
    # Hidden/Default values for other rules
    historical_turnout = st.slider("Historical Turnout % for this Unit", 0, 100, 65) / 100.0
    
    analyze_button = st.button("Analyze for Fraud Risk", use_container_width=True)

# --- Main Page ---
st.title("🚨 Intelligent Election Fraud Detection System")
st.markdown("This system uses a hybrid approach: a **Rule-Based Expert System** (with 45 compulsory rules) to identify anomalies, and a **Machine Learning Model** to calculate the final risk score based on the severity and combination of those anomalies.")

with st.expander("View All 45 Fraud Detection Rules"):
    st.dataframe(pd.DataFrame(RULES)[['id', 'severity', 'description']])

if analyze_button:
    # --- 1. Create a record from user inputs ---
    turnout_percentage = votes_cast / registered_voters if registered_voters > 0 else 0
    all_votes = [pdp_votes, apc_votes, lp_votes, other_votes]
    winning_margin_abs = max(all_votes) - sorted(all_votes)[-2]

    user_record = {
        "registered_voters": registered_voters, "accredited_voters": accredited_voters,
        "votes_cast": votes_cast, "valid_votes": valid_votes,
        "pdp_votes": pdp_votes, "apc_votes": apc_votes, "lp_votes": lp_votes, "other_votes": other_votes,
        "turnout_percentage": turnout_percentage, "historical_turnout": historical_turnout,
        "submission_delay_hours": submission_delay_hours, "form_ec8a_missing_or_altered": form_ec8a_missing_or_altered,
        "reports_of_violence": reports_of_violence, "bvas_malfunction": bvas_malfunction,
        "winning_margin_abs": winning_margin_abs,
        # Add default 'False'/'0' values for other rules to avoid errors
        "estimated_population": registered_voters * 2, "unit_win_margin": 0, "neighbor_avg_win_margin": 0,
        "historical_win_margin_abs": 0, "fails_benfords_law": False, "opening_delay_hours": 0,
        "party_agents_absent": False, "ballot_box_snatching": False, "security_personnel_present": 2,
        "results_publicly_posted": True, "manual_accreditation_alteration": False, "agents_refused_signing": 0,
        "observer_flags_irregularity": False, "observer_counts_mismatch": False, "observers_present": True,
        "reports_of_vote_buying": False, "neighbor_registered_voters": registered_voters
    }

    # --- 2. Run the Rule Engine ---
    violated_rules = evaluate_rules(user_record)
    
    # --- 3. Create Features for the ML Model ---
    model_features = pd.DataFrame([{
        'num_violations': len(violated_rules),
        'max_severity': max([r['severity'] for r in violated_rules]) if violated_rules else 0,
        'total_severity': sum([r['severity'] for r in violated_rules]),
        'num_turnout_violations': len([r for r in violated_rules if r['id'].startswith('T')]),
        'num_voting_violations': len([r for r in violated_rules if r['id'].startswith('V')]),
        'num_procedural_violations': len([r for r in violated_rules if r['id'].startswith('P')]),
    }])

    # --- 4. Get Prediction from ML Model ---
    risk_probability = model.predict_proba(model_features)[0][1] # Probability of class '1' (fraud)

    # --- 5. Display Results ---
    st.header("Analysis Results")
    
    # Determine color and risk level based on probability
    if risk_probability > 0.7:
        risk_level = "HIGH RISK"
        color = "red"
    elif risk_probability > 0.4:
        risk_level = "MODERATE RISK"
        color = "orange"
    else:
        risk_level = "LOW RISK"
        color = "green"

    # Create a gauge chart for the risk score
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_probability * 100,
        title={'text': f"Fraud Risk Score: {risk_level}"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': color},
               'steps': [
                   {'range': [0, 40], 'color': 'lightgray'},
                   {'range': [40, 70], 'color': 'gray'}],
               }))
    st.plotly_chart(fig, use_container_width=True)

    if not violated_rules:
        st.success("No anomalous indicators were found based on the provided data.")
    else:
        st.error(f"Warning: {len(violated_rules)} potential fraud indicators were triggered.")
        
        df_violations = pd.DataFrame(violated_rules)[['id', 'severity', 'description']]
        st.dataframe(df_violations.style.apply(
            lambda x: ['background-color: #FF4B4B' if x.severity > 7 else ('background-color: #FFA500' if x.severity > 4 else '') for i in x],
            axis=1
        ))