# rules_engine.py

# A compulsory list of 45 rules/facts to detect electoral fraud anomalies.
# Each rule has a unique ID, a description, a severity score (1-10), and a function to test it.

RULES = [
    # --- Turnout & Registration Anomalies (T) ---
    {"id": "T01", "severity": 10, "description": "Turnout exceeds 100% of registered voters.", "test": lambda r: r['votes_cast'] > r['registered_voters']},
    {"id": "T02", "severity": 9, "description": "Turnout is exactly 100% (highly improbable).", "test": lambda r: r['votes_cast'] == r['registered_voters'] and r['registered_voters'] > 50},
    {"id": "T03", "severity": 8, "description": "Turnout is suspiciously high (over 95%).", "test": lambda r: r['votes_cast'] / r['registered_voters'] > 0.95 if r['registered_voters'] > 0 else False},
    {"id": "T04", "severity": 5, "description": "Turnout is suspiciously low (under 10%).", "test": lambda r: r['votes_cast'] / r['registered_voters'] < 0.10 if r['registered_voters'] > 0 else False},
    {"id": "T05", "severity": 6, "description": "Turnout deviates more than 30% from historical average.", "test": lambda r: abs(r['turnout_percentage'] - r['historical_turnout']) > 0.30},
    {"id": "T06", "severity": 8, "description": "Number of accredited voters is less than total votes cast.", "test": lambda r: r['accredited_voters'] < r['votes_cast']},
    {"id": "T07", "severity": 4, "description": "Significant mismatch between registered voters and census population.", "test": lambda r: r['registered_voters'] > r['estimated_population'] * 0.8}, # More than 80% of all people are registered
    {"id": "T08", "severity": 7, "description": "Votes cast is zero, but registered voters > 0.", "test": lambda r: r['votes_cast'] == 0 and r['registered_voters'] > 0},

    # --- Voting & Results Pattern Anomalies (V) ---
    {"id": "V01", "severity": 9, "description": "One party received over 98% of the vote (extreme lack of competition).", "test": lambda r: max(r['pdp_votes'], r['apc_votes'], r['lp_votes']) / r['votes_cast'] > 0.98 if r['votes_cast'] > 0 else False},
    {"id": "V02", "severity": 7, "description": "Total party votes do not sum to total valid votes cast.", "test": lambda r: (r['pdp_votes'] + r['apc_votes'] + r['lp_votes'] + r['other_votes']) != r['valid_votes']},
    {"id": "V03", "severity": 6, "description": "Number of invalid/spoiled votes is unusually high (>10% of cast votes).", "test": lambda r: (r['votes_cast'] - r['valid_votes']) / r['votes_cast'] > 0.10 if r['votes_cast'] > 0 else False},
    {"id": "V04", "severity": 5, "description": "Vote counts for major parties are round numbers (e.g., 100, 250), suggesting fabrication.", "test": lambda r: r['pdp_votes'] % 10 == 0 and r['apc_votes'] % 10 == 0 and r['lp_votes'] % 10 == 0 and r['votes_cast'] > 50},
    {"id": "V05", "severity": 8, "description": "Results are a statistical outlier compared to neighboring polling units.", "test": lambda r: abs(r['unit_win_margin'] - r['neighbor_avg_win_margin']) > 0.40}, # Win margin differs by 40%
    {"id": "V06", "severity": 7, "description": "The number of 'other' party votes is larger than a major party's votes.", "test": lambda r: r['other_votes'] > min(r['pdp_votes'], r['apc_votes'], r['lp_votes']) and r['votes_cast'] > 100},
    {"id": "V07", "severity": 10, "description": "Total valid votes exceeds total votes cast.", "test": lambda r: r['valid_votes'] > r['votes_cast']},
    {"id": "V08", "severity": 7, "description": "Winning margin is razor-thin (1 vote) in a high-turnout unit.", "test": lambda r: r['winning_margin_abs'] == 1 and r['votes_cast'] > 200},
    {"id": "V09", "severity": 6, "description": "Vote distribution fails Benford's Law test for leading digits.", "test": lambda r: r['fails_benfords_law']},
    {"id": "V10", "severity": 5, "description": "Results show a perfect split (e.g., 50/50) between two parties.", "test": lambda r: r['pdp_votes'] == r['apc_votes'] and r['votes_cast'] > 100 and r['lp_votes'] == 0},
    {"id": "V11", "severity": 9, "description": "A candidate receives more votes than registered voters.", "test": lambda r: max(r['pdp_votes'], r['apc_votes'], r['lp_votes']) > r['registered_voters']},

    # --- Procedural & Logistical Anomalies (P) ---
    {"id": "P01", "severity": 7, "description": "Results were submitted significantly late (> 3 hours after polls closed).", "test": lambda r: r['submission_delay_hours'] > 3},
    {"id": "P02", "severity": 9, "description": "Official results form (Form EC8A) is reported missing or altered.", "test": lambda r: r['form_ec8a_missing_or_altered']},
    {"id": "P03", "severity": 6, "description": "BVAS (Bimodal Voter Accreditation System) reported malfunctioning.", "test": lambda r: r['bvas_malfunction']},
    {"id": "P04", "severity": 8, "description": "Reports of violence, voter intimidation, or coercion at the unit.", "test": lambda r: r['reports_of_violence']},
    {"id": "P05", "severity": 5, "description": "Polling unit opened significantly late (> 2 hours).", "test": lambda r: r['opening_delay_hours'] > 2},
    {"id": "P06", "severity": 7, "description": "Party agents were reportedly absent or chased away.", "test": lambda r: r['party_agents_absent']},
    {"id": "P07", "severity": 8, "description": "Ballot box snatching or stuffing reported.", "test": lambda r: r['ballot_box_snatching']},
    {"id": "P08", "severity": 4, "description": "Number of security personnel present was zero.", "test": lambda r: r['security_personnel_present'] == 0},
    {"id": "P09", "severity": 6, "description": "Results not publicly posted at the polling unit as required.", "test": lambda r: not r['results_publicly_posted']},
    {"id": "P10", "severity": 7, "description": "Accreditation numbers manually altered on forms.", "test": lambda r: r['manual_accreditation_alteration']},
    
    # --- Agent & Observer Report Anomalies (A) ---
    {"id": "A01", "severity": 7, "description": "Multiple party agents refused to sign the results form.", "test": lambda r: r['agents_refused_signing'] > 1},
    {"id": "A02", "severity": 8, "description": "Accredited domestic observers flagged the unit for irregularities.", "test": lambda r: r['observer_flags_irregularity']},
    {"id": "A03", "severity": 6, "description": "Observer reports contradict official vote counts.", "test": lambda r: r['observer_counts_mismatch']},
    {"id": "A04", "severity": 5, "description": "No independent observers were present at the polling unit.", "test": lambda r: not r['observers_present']},
    {"id": "A05", "severity": 7, "description": "Reports of vote buying heavily concentrated at this unit.", "test": lambda r: r['reports_of_vote_buying']},

    # --- Additional Statistical Checks (S) ---
    {"id": "S01", "severity": 6, "description": "The number of accredited voters is exactly equal to registered voters.", "test": lambda r: r['accredited_voters'] == r['registered_voters'] and r['registered_voters'] > 50},
    {"id": "S02", "severity": 7, "description": "The last digit of vote counts for all parties is identical and not zero.", "test": lambda r: (r['pdp_votes'] % 10 == r['apc_votes'] % 10 == r['lp_votes'] % 10) and (r['pdp_votes'] % 10 != 0) and r['votes_cast'] > 50},
    {"id": "S03", "severity": 5, "description": "Extremely low number of invalid votes (zero) in a high-turnout unit.", "test": lambda r: (r['votes_cast'] - r['valid_votes']) == 0 and r['votes_cast'] > 300},
    {"id": "S04", "severity": 8, "description": "Turnout percentage is a perfect integer (e.g., 80.00%) in a large unit.", "test": lambda r: (r['votes_cast'] / r['registered_voters']).is_integer() if r['registered_voters'] > 200 else False},
    {"id": "S05", "severity": 7, "description": "One party wins by the exact same margin as in the previous election.", "test": lambda r: r['winning_margin_abs'] == r['historical_win_margin_abs'] and r['winning_margin_abs'] > 0},
    {"id": "S06", "severity": 9, "description": "Sum of votes cast is greater than the estimated population.", "test": lambda r: r['votes_cast'] > r['estimated_population']},
    {"id": "S07", "severity": 4, "description": "One party received zero votes in a competitive area.", "test": lambda r: min(r['pdp_votes'], r['apc_votes'], r['lp_votes']) == 0 and r['votes_cast'] > 100},
    {"id": "S08", "severity": 8, "description": "Accredited voters number is a round number (e.g., 500).", "test": lambda r: r['accredited_voters'] % 100 == 0 and r['accredited_voters'] > 0},
    {"id": "S09", "severity": 7, "description": "Number of registered voters is identical to a neighboring unit.", "test": lambda r: r['registered_voters'] == r['neighbor_registered_voters']},
    {"id": "S10", "severity": 6, "description": "Vote counts are in perfect descending order (e.g., 300, 200, 100).", "test": lambda r: r['pdp_votes'] > r['apc_votes'] > r['lp_votes'] and r['pdp_votes'] % 100 == 0 and r['apc_votes'] % 100 == 0 and r['lp_votes'] % 100 == 0},
]

def evaluate_rules(record):
    """
    Runs a data record (dict) through all the rules and returns the violations.
    """
    violated_rules = []
    for rule in RULES:
        try:
            if rule["test"](record):
                violated_rules.append(rule)
        except (ZeroDivisionError, KeyError):
            # Ignore rules that can't be tested due to missing data for that record
            continue
    return violated_rules