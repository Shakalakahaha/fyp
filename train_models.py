import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os
import json
import pickle
import mysql.connector
from datetime import datetime

# Create directory for models if it doesn't exist
os.makedirs('models/default_models', exist_ok=True)

# Define the required columns based on the image
REQUIRED_FEATURES = [
    'tenure',
    'InternetService',
    'OnlineSecurity',
    'TechSupport',
    'Contract',
    'SeniorCitizen',
    'Partner',
    'Dependents',
    'OnlineBackup',
    'DeviceProtection',
    'StreamingTV',
    'StreamingMovies',
    'PaymentMethod',
    'PaperlessBilling',
    'TotalCharges',
    'MonthlyCharges'
]

# Explicitly define numerical and categorical columns
NUMERICAL_COLUMNS = ['tenure', 'TotalCharges', 'MonthlyCharges']
CATEGORICAL_COLUMNS = [col for col in REQUIRED_FEATURES if col not in NUMERICAL_COLUMNS]

TARGET_COLUMN = 'Churn'
META_COLUMN = 'customerID'

# Load your dataset
data_path = 'datasets/original/DatasetA.csv'  # Update this path if needed
print(f"Loading data from {data_path}")
data = pd.read_csv(data_path)

# Print dataset info
print(f"Dataset shape: {data.shape}")
print(f"Columns: {data.columns.tolist()}")
print(f"Target distribution: {data[TARGET_COLUMN].value_counts()}")

# Check if all required columns exist
missing_columns = [col for col in REQUIRED_FEATURES + [TARGET_COLUMN, META_COLUMN] if col not in data.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Filter to only use the required columns
filtered_data = data[[META_COLUMN] + REQUIRED_FEATURES + [TARGET_COLUMN]]
print(f"Filtered data shape: {filtered_data.shape}")

# Convert TotalCharges to numeric (it might be stored as string)
filtered_data['TotalCharges'] = pd.to_numeric(filtered_data['TotalCharges'], errors='coerce')

# Preprocess data
X = filtered_data[REQUIRED_FEATURES]
y = filtered_data[TARGET_COLUMN].map({'Yes': 1, 'No': 0})  # Convert to binary

# Handle missing values
# For categorical columns, fill with the most common value
for col in CATEGORICAL_COLUMNS:
    if X[col].isnull().any():
        X[col] = X[col].fillna(X[col].mode()[0])

# For numerical columns, fill with the median
for col in NUMERICAL_COLUMNS:
    if X[col].isnull().any():
        X[col] = X[col].fillna(X[col].median())

# Convert categorical variables to numeric
X_processed = pd.get_dummies(X, columns=CATEGORICAL_COLUMNS, drop_first=True)
print(f"Processed features shape: {X_processed.shape}")

# Print column types to verify
print("\nColumn types after preprocessing:")
for col in X.columns:
    print(f"{col}: {X[col].dtype}")

# Split data - using 80/20 split as specified
X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.2, random_state=42)
print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")

# Scale the data for neural network training
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print(f"Scaled data mean: {X_train_scaled.mean():.4f}, std: {X_train_scaled.std():.4f}")

# Define models with your specified parameters
models = {
    'gradient_boosting': GradientBoostingClassifier(
        n_estimators=400,
        learning_rate=0.01,
        max_depth=5,
        min_samples_split=2,
        subsample=0.8,
        random_state=42  # This is equivalent to replicable_training=True
    ),
    'logistic_regression': LogisticRegression(
        C=0.017,  # C parameter for regularization strength (inverse of regularization)
        penalty='l2',  # Ridge (L2) regularization
        class_weight='balanced',  # Equivalent to balance_class_distribution=True
        random_state=42,
        max_iter=1000  # Increased to ensure convergence
    ),
    'random_forest': RandomForestClassifier(
        n_estimators=150,
        max_features=6 if 6 < X_processed.shape[1] else X_processed.shape[1],  # Ensure max_features doesn't exceed column count
        max_depth=20,
        min_samples_split=5,
        class_weight='balanced',  # Equivalent to balance_class_distribution=True
        random_state=42  # Equivalent to replicable_training=True
    ),
    'neural_network': MLPClassifier(
        hidden_layer_sizes=(100, 50),
        activation='relu',  # Changed from identity to relu for better stability
        solver='adam',      # Changed from sgd to adam for better convergence
        alpha=0.01,         # Reduced alpha for better stability
        max_iter=500,       # Increased max_iter to ensure convergence
        learning_rate_init=0.001,  # Explicit learning rate
        early_stopping=True,       # Enable early stopping
        n_iter_no_change=50,       # Number of iterations with no improvement to wait before stopping
        random_state=42
    ),
    'decision_tree': DecisionTreeClassifier(
        min_samples_leaf=9,
        min_samples_split=5,
        max_depth=6,
        random_state=42
        # Note: binary_tree and majority_threshold don't have direct equivalents
        # in scikit-learn's DecisionTreeClassifier
    )
}

# Train and save models
model_results = {}

for name, model in models.items():
    print(f"\nTraining {name}...")

    try:
        # Train model - use scaled data for neural network
        if name == 'neural_network':
            print("  Using scaled data for neural network training")
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
        else:
            model.fit(X_train, y_train)
            # Evaluate model
            y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall: {recall:.4f}")
        print(f"  F1 Score: {f1:.4f}")

        # Save model using both pickle and joblib for compatibility
        # Save with joblib (recommended for scikit-learn models)
        joblib_path = f"models/default_models/{name}_joblib.pkl"
        joblib.dump(model, joblib_path)
        print(f"  Model saved with joblib to {joblib_path}")

        # Save with pickle (as a backup)
        pickle_path = f"models/default_models/{name}.pkl"
        with open(pickle_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"  Model saved with pickle to {pickle_path}")

        # Save feature names
        feature_names_path = f"models/default_models/{name}_features.pkl"
        with open(feature_names_path, 'wb') as f:
            pickle.dump(X_train.columns.tolist(), f)
        print(f"  Feature names saved to {feature_names_path}")

        # Save scaler for neural network
        if name == 'neural_network':
            scaler_path = f"models/default_models/{name}_scaler.pkl"
            joblib.dump(scaler, scaler_path)
            print(f"  Scaler saved to {scaler_path}")

        # Store results
        model_results[name] = {
            'model': model,
            'metrics': {
                'Accuracy': accuracy,
                'Precision': precision,
                'Recall': recall,
                'F1 Score': f1
            }
        }

    except Exception as e:
        print(f"Error training {name}: {str(e)}")

# Save all metrics to a JSON file for reference
metrics_json = {}
for name, result in model_results.items():
    metrics_json[name] = {
        'metrics': result['metrics']
    }

with open('models/default_models/metrics.json', 'w') as f:
    json.dump(metrics_json, f, indent=2)

print("\nAll models trained and saved successfully!")
print("Metrics saved to models/default_models/metrics.json")

# Save the column information for future reference
column_info = {
    'features': REQUIRED_FEATURES,
    'target': TARGET_COLUMN,
    'meta': META_COLUMN,
    'categorical': CATEGORICAL_COLUMNS,
    'numerical': NUMERICAL_COLUMNS
}

with open('models/default_models/column_info.json', 'w') as f:
    json.dump(column_info, f, indent=2)

print("Column information saved to models/default_models/column_info.json")