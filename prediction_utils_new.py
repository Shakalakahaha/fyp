import os
import numpy as np
import pandas as pd
import pickle
import joblib
import json
import uuid
import logging
from datetime import datetime
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load column information from JSON file
try:
    with open('models/default_models/column_info.json', 'r') as f:
        column_info = json.load(f)
    REQUIRED_COLUMNS = column_info
    logger.info("Loaded column information from models/default_models/column_info.json")
except Exception as e:
    logger.warning(f"Error loading column information: {str(e)}")
    # Default column configuration in case the file doesn't exist
    REQUIRED_COLUMNS = {
        'categorical': [
            'InternetService', 'OnlineSecurity', 'TechSupport', 'Contract',
            'Partner', 'Dependents', 'OnlineBackup', 'DeviceProtection',
            'StreamingTV', 'StreamingMovies', 'PaymentMethod', 'PaperlessBilling'
        ],
        'numerical': ['tenure', 'TotalCharges', 'MonthlyCharges', 'SeniorCitizen'],
        'meta': ['customerID']
    }
    logger.warning("Using default column configuration")

def validate_dataset(df):
    """
    Validate that the dataset has the required columns

    Args:
        df (pandas.DataFrame): The dataset to validate

    Returns:
        tuple: (is_valid, error_message, normalized_df)
    """
    logger.info(f"Validating dataset with shape: {df.shape}")
    
    # Check if the dataset has the required columns
    required_columns = REQUIRED_COLUMNS['meta'] + REQUIRED_COLUMNS['categorical'] + REQUIRED_COLUMNS['numerical']
    
    # Check if customerID is present
    if 'customerID' not in df.columns:
        # Add a dummy customerID column
        df['customerID'] = [f"CUST_{i}" for i in range(len(df))]
        logger.info("Added dummy customerID column")
    
    # Check for missing required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_message = f"Missing required columns: {missing_columns}"
        logger.error(error_message)
        return False, error_message, df
    
    # Check for missing values in required columns
    for col in required_columns:
        if df[col].isnull().any():
            error_message = f"Column {col} has missing values"
            logger.error(error_message)
            return False, error_message, df
    
    # Check data types
    for col in REQUIRED_COLUMNS['numerical']:
        if col in df.columns:
            # Try to convert to numeric
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception as e:
                error_message = f"Column {col} could not be converted to numeric: {str(e)}"
                logger.error(error_message)
                return False, error_message, df
    
    logger.info("Dataset validation successful")
    return True, "", df

def preprocess_data(df, model_type=None):
    """
    Preprocess data for prediction

    Args:
        df (pandas.DataFrame): The dataset to preprocess
        model_type (str): Type of model (for specific preprocessing)

    Returns:
        pandas.DataFrame: Preprocessed data
    """
    logger.info(f"Preprocessing data with shape: {df.shape}")
    
    # Create a copy of the dataframe
    processed_df = df.copy()
    
    # Handle categorical columns
    for col in REQUIRED_COLUMNS['categorical']:
        if col in processed_df.columns:
            # Convert to string to ensure proper handling
            processed_df[col] = processed_df[col].astype(str)
    
    # Handle numerical columns
    for col in REQUIRED_COLUMNS['numerical']:
        if col in processed_df.columns:
            # Convert to numeric
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            
            # Fill missing values with median
            if processed_df[col].isnull().any():
                median_value = processed_df[col].median()
                processed_df[col] = processed_df[col].fillna(median_value)
    
    logger.info(f"Preprocessing complete. Output shape: {processed_df.shape}")
    return processed_df

def load_model(model_path):
    """
    Load a model from a file

    Args:
        model_path (str): Path to the model file

    Returns:
        object: The loaded model
    """
    logger.info(f"Loading model from: {model_path}")
    
    # Normalize path separators
    model_path = os.path.normpath(model_path)
    
    # Check if the file exists
    if not os.path.exists(model_path):
        logger.error(f"Model file does not exist: {model_path}")
        # Try to find the file in the current directory structure
        alt_path = os.path.join(os.getcwd(), model_path)
        logger.info(f"Trying alternative path: {alt_path}")
        
        if os.path.exists(alt_path):
            model_path = alt_path
            logger.info(f"Found model at alternative path: {model_path}")
        else:
            raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Try loading with joblib first
    try:
        logger.info("Attempting to load with joblib")
        model = joblib.load(model_path)
        
        # Verify it's a valid model
        if hasattr(model, 'predict') and hasattr(model, 'predict_proba'):
            logger.info(f"Successfully loaded model with joblib: {type(model)}")
            return model
        else:
            logger.warning("Loaded object is not a valid model (missing predict methods)")
    except Exception as joblib_error:
        logger.warning(f"Joblib loading failed: {str(joblib_error)}")
    
    # If joblib fails or model is invalid, try pickle
    try:
        logger.info("Attempting to load with pickle")
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Verify it's a valid model
        if hasattr(model, 'predict') and hasattr(model, 'predict_proba'):
            logger.info(f"Successfully loaded model with pickle: {type(model)}")
            return model
        else:
            logger.warning("Loaded object is not a valid model (missing predict methods)")
    except Exception as pickle_error:
        logger.error(f"Pickle loading failed: {str(pickle_error)}")
    
    # If we get here, try loading a joblib version if we were trying a pickle version
    if '_joblib.pkl' not in model_path:
        joblib_path = model_path.replace('.pkl', '_joblib.pkl')
        if os.path.exists(joblib_path):
            logger.info(f"Trying joblib version: {joblib_path}")
            return load_model(joblib_path)
    
    # If all else fails, try a fallback model
    logger.error("Could not load a valid model, trying fallback")
    fallback_model_path = "models/default_models/decision_tree_joblib.pkl"
    if os.path.exists(fallback_model_path):
        logger.info(f"Using fallback model: {fallback_model_path}")
        return load_model(fallback_model_path)
    
    # If even the fallback fails, raise an error
    raise ValueError(f"Could not load a valid model from {model_path}")

def make_prediction(df, model):
    """
    Make predictions using the model

    Args:
        df (pandas.DataFrame): Preprocessed data
        model (object): The model to use for prediction

    Returns:
        tuple: (y_pred, churn_proba) - Predicted labels and probabilities
    """
    try:
        # Log model type
        model_type = type(model).__name__
        model_module = type(model).__module__
        logger.info(f"Making prediction with model type: {model_type} from module: {model_module}")
        
        # Check if model has necessary methods
        if not hasattr(model, 'predict'):
            logger.error(f"Model does not have predict method: {model_type}")
            raise ValueError("Model does not have predict method")
        
        if not hasattr(model, 'predict_proba'):
            logger.error(f"Model does not have predict_proba method: {model_type}")
            raise ValueError("Model does not have predict_proba method")
        
        # Extract features (exclude meta columns and target if present)
        drop_cols = REQUIRED_COLUMNS['meta'] + ['Churn'] if 'Churn' in df.columns else REQUIRED_COLUMNS['meta']
        logger.info(f"Dropping columns for prediction: {drop_cols}")
        features = df.drop(columns=drop_cols)
        
        logger.info(f"Feature columns: {features.columns.tolist()}")
        logger.info(f"Feature shape: {features.shape}")
        
        # Try to determine the model name from the model type
        model_name = None
        if 'DecisionTree' in model_type:
            model_name = 'decision_tree'
        elif 'RandomForest' in model_type:
            model_name = 'random_forest'
        elif 'GradientBoosting' in model_type:
            model_name = 'gradient_boosting'
        elif 'LogisticRegression' in model_type:
            model_name = 'logistic_regression'
        elif 'MLP' in model_type:
            model_name = 'neural_network'
        
        # For neural network, try to load the scaler
        scaler = None
        if model_name == 'neural_network':
            scaler_path = f"models/default_models/{model_name}_scaler.pkl"
            if os.path.exists(scaler_path):
                try:
                    scaler = joblib.load(scaler_path)
                    logger.info(f"Loaded scaler from {scaler_path}")
                except Exception as e:
                    logger.warning(f"Error loading scaler: {str(e)}")
        
        # Try to load feature names from file
        if model_name:
            feature_names_path = f"models/default_models/{model_name}_features.pkl"
            if os.path.exists(feature_names_path):
                try:
                    with open(feature_names_path, 'rb') as f:
                        training_features = pickle.load(f)
                    logger.info(f"Loaded feature names from {feature_names_path}")
                    
                    # Convert features to match training features
                    features_encoded = pd.get_dummies(features)
                    
                    # Add missing columns
                    for col in training_features:
                        if col not in features_encoded.columns:
                            features_encoded[col] = 0
                    
                    # Reorder columns to match training features
                    features_encoded = features_encoded[training_features]
                    
                    logger.info(f"Encoded features shape: {features_encoded.shape}")
                    features = features_encoded
                except Exception as e:
                    logger.warning(f"Error loading feature names: {str(e)}")
        
        # Prepare features for prediction
        prediction_features = features
        
        # Apply scaling for neural network if available
        if model_name == 'neural_network' and scaler is not None:
            try:
                prediction_features = scaler.transform(features)
                logger.info(f"Applied scaling to features for neural network prediction")
            except Exception as e:
                logger.warning(f"Error applying scaling: {str(e)}. Using unscaled features.")
        
        # Check if model is a numpy array (which can happen if the model was incorrectly loaded)
        if isinstance(model, np.ndarray):
            logger.error("Model is a numpy array, not a valid model object")
            raise ValueError("Invalid model object: model is a numpy array")
        
        # Make prediction
        logger.info("Making prediction")
        y_proba = model.predict_proba(prediction_features)
        logger.info(f"Prediction probabilities shape: {y_proba.shape}")
        
        # Get the probability of churn (class 1)
        churn_proba = y_proba[:, 1]
        logger.info(f"Churn probabilities shape: {churn_proba.shape}")
        
        # Convert probabilities to binary predictions (threshold 0.5)
        y_pred = (churn_proba >= 0.5).astype(int)
        logger.info(f"Predictions shape: {y_pred.shape}")
        
        return y_pred, y_proba
    
    except Exception as e:
        logger.error(f"Error in make_prediction: {str(e)}")
        raise

def get_feature_importance(model, feature_names, df, y_pred):
    """
    Get feature importance for the model

    Args:
        model (object): The trained model
        feature_names (list): List of feature names
        df (pandas.DataFrame): The dataset used for prediction
        y_pred (numpy.ndarray): The predicted values

    Returns:
        list: List of feature importance dictionaries
    """
    try:
        logger.info("Getting feature importance")
        
        # Check if model has feature_importances_ attribute (tree-based models)
        if hasattr(model, 'feature_importances_'):
            logger.info("Using feature_importances_ attribute")
            importances = model.feature_importances_
            
            # Create a list of dictionaries with feature name and importance
            feature_importance = [
                {'feature': feature_names[i], 'importance': float(importances[i])}
                for i in range(len(feature_names))
            ]
            
            # Sort by importance (descending)
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            
            # Take top 10 features
            return feature_importance[:10]
        
        # Check if model has coef_ attribute (linear models)
        elif hasattr(model, 'coef_'):
            logger.info("Using coef_ attribute")
            coefficients = model.coef_[0] if model.coef_.ndim > 1 else model.coef_
            
            # Create a list of dictionaries with feature name and importance
            feature_importance = [
                {'feature': feature_names[i], 'importance': abs(float(coefficients[i]))}
                for i in range(len(feature_names))
            ]
            
            # Sort by importance (descending)
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            
            # Take top 10 features
            return feature_importance[:10]
        
        else:
            logger.warning("Model does not have feature_importances_ or coef_ attribute")
            # Return empty list if feature importance is not available
            return []
    
    except Exception as e:
        logger.error(f"Error getting feature importance: {str(e)}")
        return []

def save_prediction_results(df, y_pred, churn_proba, prediction_name, user_type, user_id):
    """
    Save prediction results to a file

    Args:
        df (pandas.DataFrame): The original dataset
        y_pred (numpy.ndarray): The predicted values
        churn_proba (numpy.ndarray): The predicted probabilities
        prediction_name (str): Name of the prediction
        user_type (str): Type of user (dev or user)
        user_id (int): ID of the user

    Returns:
        tuple: (result_path, result_filename)
    """
    try:
        logger.info(f"Saving prediction results for {prediction_name}")
        
        # Ensure inputs are of the correct type
        if not isinstance(y_pred, np.ndarray):
            logger.warning(f"y_pred is not a numpy array: {type(y_pred)}. Converting to numpy array.")
            y_pred = np.array(y_pred)
        
        if not isinstance(churn_proba, np.ndarray):
            logger.warning(f"churn_proba is not a numpy array: {type(churn_proba)}. Converting to numpy array.")
            churn_proba = np.array(churn_proba)
        
        logger.info(f"DataFrame shape: {df.shape}, y_pred shape: {y_pred.shape}, churn_proba shape: {churn_proba.shape}")
        
        # Create a copy of the original data
        result_df = df.copy()
        
        # Add prediction columns
        result_df['Churn_Prediction'] = y_pred
        
        # Handle different churn_proba formats
        if churn_proba.ndim > 1 and churn_proba.shape[1] > 1:
            logger.info(f"Using column 1 of churn_proba with shape {churn_proba.shape}")
            result_df['Churn_Probability'] = churn_proba[:, 1]
        else:
            logger.info(f"Using churn_proba directly with shape {churn_proba.shape}")
            result_df['Churn_Probability'] = churn_proba
        
        # Map binary predictions to Yes/No
        result_df['Churn_Prediction'] = result_df['Churn_Prediction'].map({1: 'Yes', 0: 'No'})
        
        # Ensure user_type is a string
        if not isinstance(user_type, str):
            logger.warning(f"user_type is not a string: {type(user_type)}. Converting to string.")
            user_type = str(user_type)
        
        # Normalize user_type to either 'dev' or 'user'
        if user_type.lower() in ['dev', 'developer', 'admin', 'administrator']:
            directory_type = 'dev'
        else:
            directory_type = 'user'
        
        # Create directory if it doesn't exist
        result_dir = os.path.join('datasets', directory_type, 'predictionResult')
        os.makedirs(result_dir, exist_ok=True)
        logger.info(f"Saving results to directory: {result_dir}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Ensure prediction_name is a string
        if not isinstance(prediction_name, str):
            logger.warning(f"prediction_name is not a string: {type(prediction_name)}. Converting to string.")
            prediction_name = str(prediction_name)
        
        # Clean up the prediction name for use in a filename
        safe_name = ''.join(c if c.isalnum() else '_' for c in prediction_name)
        result_filename = f"{safe_name}_{timestamp}_{unique_id}.csv"
        result_path = os.path.join(result_dir, result_filename)
        logger.info(f"Result file path: {result_path}")
        
        # Save to CSV
        try:
            # Convert any non-serializable objects to strings
            for col in result_df.columns:
                if result_df[col].dtype == 'object':
                    result_df[col] = result_df[col].astype(str)
            
            result_df.to_csv(result_path, index=False)
            logger.info(f"Successfully saved prediction results to {result_path}")
        except Exception as csv_error:
            logger.error(f"Error saving to CSV: {str(csv_error)}")
            # Try a different approach
            logger.info("Trying alternative approach to save results")
            result_df.to_csv(result_path, index=False, encoding='utf-8')
        
        return result_path, result_filename
    
    except Exception as e:
        logger.error(f"Error saving prediction results: {str(e)}")
        logger.exception("Detailed traceback:")
        raise

def get_prediction_summary(y_pred):
    """
    Get summary statistics for the prediction

    Args:
        y_pred (numpy.ndarray): The predicted values

    Returns:
        dict: Summary statistics
    """
    try:
        # Ensure y_pred is a numpy array
        if not isinstance(y_pred, np.ndarray):
            logger.warning(f"y_pred is not a numpy array: {type(y_pred)}. Converting to numpy array.")
            y_pred = np.array(y_pred)
        
        # Count total records
        total_records = len(y_pred)
        
        # Count churn and no churn
        churn_count = np.sum(y_pred)
        no_churn_count = total_records - churn_count
        
        # Calculate churn rate
        churn_rate = churn_count / total_records if total_records > 0 else 0
        
        return {
            'total_records': int(total_records),
            'churn_distribution': {
                'churn': int(churn_count),
                'no_churn': int(no_churn_count),
                'churn_rate': float(churn_rate)
            }
        }
    except Exception as e:
        logger.error(f"Error getting prediction summary: {str(e)}")
        return {
            'total_records': 0,
            'churn_distribution': {
                'churn': 0,
                'no_churn': 0,
                'churn_rate': 0.0
            }
        }

def process_prediction_request(file_path, model_id, prediction_name, user_type, user_id, conn):
    """
    Process a prediction request

    Args:
        file_path (str): Path to the input file
        model_id (int): ID of the model to use
        prediction_name (str): Name of the prediction
        user_type (str): Type of user (dev or user)
        user_id (int): ID of the user
        conn (connection): Database connection

    Returns:
        dict: Prediction results
    """
    logger.info(f"Processing prediction request")
    logger.info(f"Parameters: file_path={file_path}, model_id={model_id}, prediction_name={prediction_name}, user_type={user_type}, user_id={user_id}")
    
    try:
        # Convert model_id to int if it's a string
        if isinstance(model_id, str):
            try:
                model_id = int(model_id)
                logger.info(f"Converted model_id to int: {model_id}")
            except ValueError:
                logger.error(f"Failed to convert model_id to int: {model_id}")
                return {'status': 'error', 'message': f'Invalid model ID: {model_id}'}
        
        # Get model information from database
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT m.id, m.name, m.file_path as path, m.model_type_id, mt.name as model_type
        FROM models m
        JOIN modeltypes mt ON m.model_type_id = mt.id
        WHERE m.id = %s
        """
        cursor.execute(query, (model_id,))
        model_info = cursor.fetchone()
        
        if not model_info:
            logger.error(f"Model not found with ID: {model_id}")
            return {'status': 'error', 'message': 'Model not found'}
        
        logger.info(f"Found model: {model_info['name']} (ID: {model_info['id']}, Type: {model_info['model_type']})")
        
        # Load the dataset
        logger.info(f"Loading dataset from: {file_path}")
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            logger.error(f"Unsupported file format: {file_extension}")
            return {'status': 'error', 'message': 'Unsupported file format'}
        
        logger.info(f"Loaded dataset with shape: {df.shape}")
        
        # Validate the dataset
        is_valid, error_message, normalized_df = validate_dataset(df)
        if not is_valid:
            logger.error(f"Dataset validation failed: {error_message}")
            return {'status': 'error', 'message': error_message}
        
        # Preprocess the data
        processed_df = preprocess_data(normalized_df, model_info['model_type'])
        
        # Load the model
        model_path = model_info['path']
        logger.info(f"Loading model from path: {model_path}")
        
        try:
            model = load_model(model_path)
            logger.info(f"Successfully loaded model: {type(model)}")
        except Exception as model_error:
            logger.error(f"Error loading model: {str(model_error)}")
            return {'status': 'error', 'message': f'Error loading model: {str(model_error)}'}
        
        # Make prediction
        try:
            y_pred, churn_proba = make_prediction(processed_df, model)
            logger.info(f"Successfully made prediction. y_pred shape: {y_pred.shape}, churn_proba shape: {churn_proba.shape}")
        except Exception as pred_error:
            logger.error(f"Error making prediction: {str(pred_error)}")
            return {'status': 'error', 'message': f'Error making prediction: {str(pred_error)}'}
        
        # Get feature importance
        feature_names = processed_df.drop(columns=REQUIRED_COLUMNS['meta']).columns.tolist()
        feature_importance = get_feature_importance(model, feature_names, processed_df, y_pred)
        
        # Save prediction results
        try:
            result_path, result_filename = save_prediction_results(
                normalized_df, y_pred, churn_proba, prediction_name, user_type, user_id
            )
            logger.info(f"Saved prediction results to: {result_path}")
        except Exception as save_error:
            logger.error(f"Error saving prediction results: {str(save_error)}")
            return {'status': 'error', 'message': f'Error saving prediction results: {str(save_error)}'}
        
        # Get prediction summary
        summary = get_prediction_summary(y_pred)
        logger.info(f"Prediction summary: {summary}")
        
        # Record prediction in database
        try:
            # Prepare input data JSON
            input_data_json = json.dumps({
                'file_name': os.path.basename(file_path),
                'total_records': int(summary['total_records'])
            })
            
            # Prepare result JSON
            result_json = json.dumps({
                'churn_count': int(summary['churn_distribution']['churn']),
                'no_churn_count': int(summary['churn_distribution']['no_churn']),
                'churn_percentage': float(summary['churn_distribution']['churn_rate'] * 100)
            })
            
            # Use the correct query based on user type
            if user_type == 'dev':
                query = """
                INSERT INTO predictions (
                    prediction_name, developer_id, model_id, upload_dataset_path, result_dataset_path,
                    input_data, result, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """
                logger.info(f"Using developer query with developer_id: {user_id}")
            else:
                query = """
                INSERT INTO predictions (
                    prediction_name, user_id, model_id, upload_dataset_path, result_dataset_path,
                    input_data, result, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """
                logger.info(f"Using user query with user_id: {user_id}")
            
            # Prepare query parameters
            query_params = (
                str(prediction_name),
                int(user_id),
                int(model_id),
                str(os.path.basename(file_path)),
                str(result_filename),
                input_data_json,
                result_json
            )
            
            # Log query parameters
            logger.info(f"Query parameters:")
            logger.info(f"  prediction_name: {str(prediction_name)} (type: {type(prediction_name)})")
            logger.info(f"  user_id: {int(user_id)} (type: {type(int(user_id))})")
            logger.info(f"  model_id: {int(model_id)} (type: {type(int(model_id))})")
            logger.info(f"  file_path: {str(os.path.basename(file_path))} (type: {type(str(os.path.basename(file_path)))})")
            logger.info(f"  result_filename: {str(result_filename)} (type: {type(str(result_filename))})")
            
            # Execute query
            cursor.execute(query, query_params)
            prediction_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Recorded prediction in database with ID: {prediction_id}")
            
        except Exception as db_error:
            logger.error(f"Error recording prediction in database: {str(db_error)}")
            logger.exception("Detailed traceback:")
            return {'status': 'error', 'message': f'Error recording prediction in database: {str(db_error)}'}
        
        # Return success response
        return {
            'status': 'success',
            'data': {
                'prediction_id': prediction_id,
                'prediction_name': prediction_name,
                'model_id': model_id,
                'model_name': model_info['name'],
                'total_records': summary['total_records'],
                'churn_distribution': summary['churn_distribution'],
                'feature_importance': feature_importance,
                'download_url': f'/api/predictions/{prediction_id}/download',
                'created_at': datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        logger.error(f"Error processing prediction: {str(e)}")
        logger.exception("Detailed traceback:")
        return {'status': 'error', 'message': str(e)}
