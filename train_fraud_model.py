# train_fraud_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib
from rules_engine import evaluate_rules

print("Loading data...")
df = pd.read_csv("fraud_mock_data.csv")

# --- Feature Engineering using the Rule Engine ---
print("Applying rules engine to generate features...")
features = []
for index, row in df.iterrows():
    record_dict = row.to_dict()
    violated_rules = evaluate_rules(record_dict)
    
    # Create features based on the violations
    features.append({
        'num_violations': len(violated_rules),
        'max_severity': max([r['severity'] for r in violated_rules]) if violated_rules else 0,
        'total_severity': sum([r['severity'] for r in violated_rules]),
        'num_turnout_violations': len([r for r in violated_rules if r['id'].startswith('T')]),
        'num_voting_violations': len([r for r in violated_rules if r['id'].startswith('V')]),
        'num_procedural_violations': len([r for r in violated_rules if r['id'].startswith('P')]),
    })

df_features = pd.DataFrame(features)
print("Feature generation complete.")

# --- Model Training ---
X = df_features
y = df['is_fraudulent']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

print("Training Logistic Regression model...")
model = LogisticRegression(class_weight='balanced')
model.fit(X_train, y_train)

# --- Evaluate and Save ---
print("Model evaluation:")
predictions = model.predict(X_test)
print(classification_report(y_test, predictions))

joblib.dump(model, 'fraud_model.joblib')
print("Model saved to fraud_model.joblib")