# create_fraud_mock_data.py
import pandas as pd
import numpy as np
import random
from rules_engine import RULES

def generate_base_record():
    """Generates a single, plausible-looking clean record."""
    registered = np.random.randint(200, 800)
    turnout = np.random.uniform(0.35, 0.75)
    cast = int(registered * turnout)
    accredited = cast + np.random.randint(0, 5) # Slightly more accredited than cast
    valid = cast - np.random.randint(0, int(cast * 0.05)) # Small number of invalid votes

    # Plausible vote split
    votes = np.random.multinomial(valid, pvals=[0.4, 0.3, 0.2, 0.1])
    
    pdp, apc, lp, other = votes[0], votes[1], votes[2], votes[3]

    return {
        "registered_voters": registered,
        "accredited_voters": accredited,
        "votes_cast": cast,
        "valid_votes": valid,
        "pdp_votes": pdp, "apc_votes": apc, "lp_votes": lp, "other_votes": other,
        "turnout_percentage": turnout,
        "historical_turnout": turnout + np.random.uniform(-0.1, 0.1),
        "estimated_population": registered * 2 + np.random.randint(-50, 50),
        "unit_win_margin": (max(votes) - sorted(votes)[-2]) / valid if valid > 0 else 0,
        "neighbor_avg_win_margin": (max(votes) - sorted(votes)[-2]) / valid + np.random.uniform(-0.1, 0.1) if valid > 0 else 0,
        "winning_margin_abs": max(votes) - sorted(votes)[-2] if valid > 0 else 0,
        "historical_win_margin_abs": max(votes) - sorted(votes)[-2] + np.random.randint(-10, 10) if valid > 0 else 0,
        "fails_benfords_law": random.choice([True, False]),
        "submission_delay_hours": np.random.uniform(0.5, 2.0),
        "form_ec8a_missing_or_altered": False,
        "bvas_malfunction": False,
        "reports_of_violence": False,
        "opening_delay_hours": np.random.uniform(0, 1.5),
        "party_agents_absent": False,
        "ballot_box_snatching": False,
        "security_personnel_present": np.random.randint(1, 4),
        "results_publicly_posted": True,
        "manual_accreditation_alteration": False,
        "agents_refused_signing": np.random.randint(0, 1),
        "observer_flags_irregularity": False,
        "observer_counts_mismatch": False,
        "observers_present": True,
        "reports_of_vote_buying": False,
        "neighbor_registered_voters": registered + np.random.randint(-20, 20),
        "is_fraudulent": 0 # This is a clean record
    }

def generate_fraudulent_record(base_record):
    """Takes a record and modifies it to be fraudulent."""
    record = base_record.copy()
    record["is_fraudulent"] = 1
    num_violations = np.random.randint(3, 10) # Each fraudulent record will violate 3-10 rules
    
    # Intentionally violate some rules
    for _ in range(num_violations):
        rule_to_violate = random.choice(RULES)
        # This is a simplified way to trigger violations. A real one would be more complex.
        if rule_to_violate['id'] == 'T01': record['votes_cast'] = record['registered_voters'] + 50
        if rule_to_violate['id'] == 'T06': record['accredited_voters'] = record['votes_cast'] - 20
        if rule_to_violate['id'] == 'V01': record['pdp_votes'] = record['valid_votes']; record['apc_votes'] = 0; record['lp_votes'] = 0
        if rule_to_violate['id'] == 'V02': record['valid_votes'] += 100
        if rule_to_violate['id'] == 'P01': record['submission_delay_hours'] = 5
        if rule_to_violate['id'] == 'P02': record['form_ec8a_missing_or_altered'] = True
        if rule_to_violate['id'] == 'P04': record['reports_of_violence'] = True
        # ... add more triggers for other rules as needed
        
    return record


print("Generating mock data for fraud detection...")
records = []
for i in range(500): # Generate 500 clean and 500 fraudulent records
    clean_record = generate_base_record()
    records.append(clean_record)
    records.append(generate_fraudulent_record(clean_record))

df = pd.DataFrame(records)
df.to_csv("fraud_mock_data.csv", index=False)
print("Data saved to fraud_mock_data.csv")