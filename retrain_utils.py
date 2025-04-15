"""
Utility functions for model retraining
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle
import logging
import json
from datetime import datetime
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection settings
DB_USER = 'root'
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_NAME = 'fyp_db'

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Define the required columns based on train_models.py
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

def validate_dataset(file_path):
    """
    Validate the uploaded dataset

    Args:
        file_path (str): Path to the dataset file

    Returns:
        tuple: (is_valid, message)
    """
    try:
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.csv':
            data = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            data = pd.read_excel(file_path)
        else:
            return False, f"Unsupported file format: {file_ext}. Please upload a CSV or Excel file."

        # Check required columns
        missing_columns = [col for col in REQUIRED_FEATURES + [TARGET_COLUMN, META_COLUMN] if col not in data.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"

        # Check data types
        # Convert TotalCharges to numeric (it might be stored as string)
        data['TotalCharges'] = pd.to_numeric(data['TotalCharges'], errors='coerce')

        # Check for missing values
        missing_values = data[REQUIRED_FEATURES + [TARGET_COLUMN]].isnull().sum()
        if missing_values.sum() > 0:
            missing_cols = [f"{col} ({count} missing)" for col, count in missing_values.items() if count > 0]
            logger.warning(f"Dataset has missing values: {missing_cols}")
            # We'll handle missing values during preprocessing, so this is just a warning

        # Check target column values
        valid_target_values = ['Yes', 'No', 1, 0, True, False]
        invalid_targets = [val for val in data[TARGET_COLUMN].unique() if str(val).lower() not in [str(v).lower() for v in valid_target_values]]
        if invalid_targets:
            return False, f"Invalid values in Churn column: {invalid_targets}. Expected: Yes/No or 1/0 or True/False"

        return True, "Dataset is valid"

    except Exception as e:
        logger.error(f"Error validating dataset: {str(e)}")
        return False, f"Error validating dataset: {str(e)}"

def get_latest_dataset(company_id):
    """
    Get the latest dataset for a company

    Args:
        company_id (str): Company ID

    Returns:
        dict: Dataset information or None if not found
    """
    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # First, try to get the latest combined dataset for the company
            query = """
            SELECT id, file_path, name
            FROM datasets
            WHERE company_id = :company_id AND is_combined = 1
            ORDER BY created_at DESC
            LIMIT 1
            """
            result = conn.execute(text(query), {"company_id": company_id})
            dataset = result.fetchone()

            if dataset:
                logger.info(f"Found latest combined dataset for company {company_id}: {dataset[0]}")
                return {
                    "id": dataset[0],
                    "file_path": dataset[1],
                    "name": dataset[2],
                    "type": "combined"
                }

            # If no combined dataset, get the original dataset
            query = """
            SELECT id, file_path, name
            FROM datasets
            WHERE is_original = 1
            LIMIT 1
            """
            result = conn.execute(text(query))
            dataset = result.fetchone()

            if dataset:
                logger.info(f"No combined dataset found for company {company_id}, using original dataset: {dataset[0]}")
                return {
                    "id": dataset[0],
                    "file_path": dataset[1],
                    "name": dataset[2],
                    "type": "original"
                }

            return None

    except Exception as e:
        logger.error(f"Error getting latest dataset: {str(e)}")
        return None

def combine_datasets(new_dataset_path, existing_dataset_path, output_path):
    """
    Combine the new dataset with an existing dataset

    Args:
        new_dataset_path (str): Path to the new dataset
        existing_dataset_path (str): Path to the existing dataset
        output_path (str): Path to save the combined dataset

    Returns:
        tuple: (success, message, total_records)
    """
    try:
        logger.info(f"Combining datasets: new={new_dataset_path}, existing={existing_dataset_path}")

        # Check if files exist
        if not os.path.exists(new_dataset_path):
            error_msg = f"New dataset file not found: {new_dataset_path}"
            logger.error(error_msg)
            return False, error_msg, 0

        if not os.path.exists(existing_dataset_path):
            error_msg = f"Existing dataset file not found: {existing_dataset_path}"
            logger.error(error_msg)
            return False, error_msg, 0

        # Load datasets
        new_ext = os.path.splitext(new_dataset_path)[1].lower()
        existing_ext = os.path.splitext(existing_dataset_path)[1].lower()

        try:
            if new_ext == '.csv':
                new_data = pd.read_csv(new_dataset_path)
                logger.info(f"Loaded new dataset (CSV): {new_dataset_path}, shape: {new_data.shape}")
            else:
                new_data = pd.read_excel(new_dataset_path)
                logger.info(f"Loaded new dataset (Excel): {new_dataset_path}, shape: {new_data.shape}")
        except Exception as e:
            error_msg = f"Error loading new dataset: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, 0

        try:
            if existing_ext == '.csv':
                existing_data = pd.read_csv(existing_dataset_path)
                logger.info(f"Loaded existing dataset (CSV): {existing_dataset_path}, shape: {existing_data.shape}")
            else:
                existing_data = pd.read_excel(existing_dataset_path)
                logger.info(f"Loaded existing dataset (Excel): {existing_dataset_path}, shape: {existing_data.shape}")
        except Exception as e:
            error_msg = f"Error loading existing dataset: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, 0

        # Check for required columns
        required_cols = REQUIRED_FEATURES + [TARGET_COLUMN, META_COLUMN]

        missing_cols_new = [col for col in required_cols if col not in new_data.columns]
        if missing_cols_new:
            error_msg = f"New dataset is missing required columns: {missing_cols_new}"
            logger.error(error_msg)
            return False, error_msg, 0

        missing_cols_existing = [col for col in required_cols if col not in existing_data.columns]
        if missing_cols_existing:
            error_msg = f"Existing dataset is missing required columns: {missing_cols_existing}"
            logger.error(error_msg)
            return False, error_msg, 0

        # Ensure both datasets have the same columns
        new_data = new_data[required_cols]
        existing_data = existing_data[required_cols]

        logger.info(f"New dataset records: {len(new_data)}, Existing dataset records: {len(existing_data)}")

        # Combine datasets
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        logger.info(f"Combined dataset before deduplication: {len(combined_data)} records")

        # Remove duplicates based on customerID
        duplicates_count = combined_data.duplicated(subset=[META_COLUMN]).sum()
        logger.info(f"Found {duplicates_count} duplicate customer IDs")

        combined_data.drop_duplicates(subset=[META_COLUMN], keep='last', inplace=True)
        logger.info(f"Combined dataset after deduplication: {len(combined_data)} records")

        # Save combined dataset
        combined_data.to_csv(output_path, index=False)
        logger.info(f"Saved combined dataset to {output_path}")

        return True, "Datasets combined successfully", len(combined_data)

    except Exception as e:
        logger.error(f"Error combining datasets: {str(e)}")
        return False, f"Error combining datasets: {str(e)}", 0

def train_gbm_model(dataset_path, output_model_path, output_features_path):
    """
    Train a Gradient Boosting Machine model

    Args:
        dataset_path (str): Path to the dataset
        output_model_path (str): Path to save the trained model
        output_features_path (str): Path to save the feature names

    Returns:
        tuple: (success, message, metrics, feature_importance)
    """
    try:
        # Load dataset
        file_ext = os.path.splitext(dataset_path)[1].lower()
        if file_ext == '.csv':
            data = pd.read_csv(dataset_path)
        else:
            data = pd.read_excel(dataset_path)

        # Filter to only use the required columns
        filtered_data = data[[META_COLUMN] + REQUIRED_FEATURES + [TARGET_COLUMN]]

        # Convert TotalCharges to numeric (it might be stored as string)
        filtered_data['TotalCharges'] = pd.to_numeric(filtered_data['TotalCharges'], errors='coerce')

        # Preprocess data
        X = filtered_data[REQUIRED_FEATURES]
        y = filtered_data[TARGET_COLUMN]

        # Convert target to binary if it's not already
        if y.dtype == object:
            y = y.map({'Yes': 1, 'No': 0})

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

        # Split data - using 80/20 split as specified
        X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.2, random_state=42)

        # Create and train the model with parameters from train_models.py
        model = GradientBoostingClassifier(
            n_estimators=400,
            learning_rate=0.01,
            max_depth=5,
            min_samples_split=2,
            subsample=0.8,
            random_state=42
        )

        model.fit(X_train, y_train)

        # Evaluate model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        # Get feature importance
        feature_importance = []
        for i, feature in enumerate(X_processed.columns):
            feature_importance.append({
                "feature": feature,
                "importance": float(model.feature_importances_[i])
            })

        # Sort by importance
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)

        # Save model
        with open(output_model_path, 'wb') as f:
            pickle.dump(model, f)

        # Save feature names
        with open(output_features_path, 'wb') as f:
            pickle.dump(X_processed.columns.tolist(), f)

        # Create metrics
        metrics = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1)
        }

        return True, "Model trained successfully", metrics, feature_importance

    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return False, f"Error training model: {str(e)}", {}, []

def get_next_model_version(company_id, model_type_id):
    """
    Get the next version number for a model

    Args:
        company_id (str): Company ID
        model_type_id (int): Model type ID

    Returns:
        str: Next version number
    """
    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            query = """
            SELECT MAX(CAST(version AS UNSIGNED)) as max_version
            FROM models
            WHERE company_id = :company_id AND model_type_id = :model_type_id
            """
            result = conn.execute(text(query), {
                "company_id": company_id,
                "model_type_id": model_type_id
            })
            row = result.fetchone()

            if row and row[0]:
                return str(int(row[0]) + 1)

            return "2"  # Start with version 2 for retrained models (version 1 is the default model)

    except Exception as e:
        logger.error(f"Error getting next model version: {str(e)}")
        return "2"  # Default to version 2 if there's an error

def get_previous_model_metrics(company_id, model_type_id):
    """
    Get metrics for the previous version of a model

    Args:
        company_id (str): Company ID
        model_type_id (int): Model type ID

    Returns:
        dict: Metrics or default values if not found
    """
    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            query = """
            SELECT m.id, m.version
            FROM models m
            WHERE m.company_id = :company_id AND m.model_type_id = :model_type_id
            ORDER BY CAST(m.version AS UNSIGNED) DESC
            LIMIT 1
            """
            result = conn.execute(text(query), {
                "company_id": company_id,
                "model_type_id": model_type_id
            })
            model = result.fetchone()

            if not model:
                # Try to get the default model
                query = """
                SELECT m.id, m.version
                FROM models m
                WHERE m.is_default = 1 AND m.model_type_id = :model_type_id
                LIMIT 1
                """
                result = conn.execute(text(query), {
                    "model_type_id": model_type_id
                })
                model = result.fetchone()

            if model:
                model_id = model[0]

                query = """
                SELECT accuracy, `precision`, recall, f1_score
                FROM modelmetrics
                WHERE model_id = :model_id
                """
                result = conn.execute(text(query), {"model_id": model_id})
                metrics = result.fetchone()

                if metrics:
                    return {
                        "accuracy": float(metrics[0]),
                        "precision": float(metrics[1]),
                        "recall": float(metrics[2]),
                        "f1_score": float(metrics[3])
                    }

            # Default values if no previous metrics found
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0
            }

    except Exception as e:
        logger.error(f"Error getting previous model metrics: {str(e)}")
        # Default values if there's an error
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0
        }

def register_model_in_db(company_id, model_type_id, model_name, version, file_path, metrics, dataset_id):
    """
    Register a new model in the database

    Args:
        company_id (str): Company ID
        model_type_id (int): Model type ID
        model_name (str): Model name
        version (str): Model version
        file_path (str): Path to the model file
        metrics (dict): Model metrics
        dataset_id (int): ID of the training dataset

    Returns:
        tuple: (success, message, model_id)
    """
    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Insert model record
            query = """
            INSERT INTO models (
                model_type_id, name, version, file_path,
                is_default, company_id, training_dataset_id, created_at, updated_at
            ) VALUES (
                :model_type_id, :name, :version, :file_path,
                0, :company_id, :dataset_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
            conn.execute(text(query), {
                "model_type_id": model_type_id,
                "name": model_name,
                "version": version,
                "file_path": file_path,
                "company_id": company_id,
                "dataset_id": dataset_id
            })

            # Get the model ID
            query = """
            SELECT id FROM models
            WHERE company_id = :company_id AND model_type_id = :model_type_id AND version = :version
            """
            result = conn.execute(text(query), {
                "company_id": company_id,
                "model_type_id": model_type_id,
                "version": version
            })
            model_id = result.fetchone()[0]

            # Insert metrics
            query = """
            INSERT INTO modelmetrics (
                model_id, accuracy, `precision`, recall,
                f1_score, additional_metrics, created_at
            ) VALUES (
                :model_id, :accuracy, :precision, :recall,
                :f1_score, :additional_metrics, CURRENT_TIMESTAMP
            )
            """
            conn.execute(text(query), {
                "model_id": model_id,
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"],
                "additional_metrics": json.dumps({"metrics": metrics})
            })

            conn.commit()

            return True, "Model registered successfully", model_id

    except Exception as e:
        logger.error(f"Error registering model: {str(e)}")
        return False, f"Error registering model: {str(e)}", None

def register_dataset_in_db(company_id, name, file_path, is_uploaded=False, is_combined=False, parent_dataset_id=None):
    """
    Register a dataset in the database

    Args:
        company_id (str): Company ID
        name (str): Dataset name
        file_path (str): Path to the dataset file
        is_uploaded (bool): Whether this is an uploaded dataset
        is_combined (bool): Whether this is a combined dataset
        parent_dataset_id (int): ID of the parent dataset

    Returns:
        tuple: (success, message, dataset_id)
    """
    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            query = """
            INSERT INTO datasets (
                company_id, name, file_path,
                is_original, is_uploaded, is_combined,
                parent_dataset_id, created_at
            ) VALUES (
                :company_id, :name, :file_path,
                0, :is_uploaded, :is_combined,
                :parent_dataset_id, CURRENT_TIMESTAMP
            )
            """
            conn.execute(text(query), {
                "company_id": company_id,
                "name": name,
                "file_path": file_path,
                "is_uploaded": 1 if is_uploaded else 0,
                "is_combined": 1 if is_combined else 0,
                "parent_dataset_id": parent_dataset_id
            })

            # Get the dataset ID
            query = """
            SELECT LAST_INSERT_ID()
            """
            result = conn.execute(text(query))
            dataset_id = result.fetchone()[0]

            conn.commit()

            return True, "Dataset registered successfully", dataset_id

    except Exception as e:
        logger.error(f"Error registering dataset: {str(e)}")
        return False, f"Error registering dataset: {str(e)}", None
