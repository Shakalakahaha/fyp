import os
import pickle
import pandas as pd
from datetime import datetime
import sqlite3
from sqlalchemy import create_engine, text
import json
import logging
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection settings
DB_USER = 'root'
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_NAME = 'fyp_db'

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Base paths - relative to the project root
# These paths don't include the full system path, just the path relative to the project root
MODELS_DIR = 'models'
DEFAULT_MODELS_DIR = os.path.join(MODELS_DIR, 'default_models')
RETRAINED_MODELS_DIR = os.path.join(MODELS_DIR, 'retrained_models')
DATASETS_DIR = 'datasets'
ORIGINAL_DATASET = 'DatasetA.csv'

# Default system company for initialization (needed for foreign key constraints)
DEFAULT_COMPANY_ID = 'SYS000'
DEFAULT_COMPANY_NAME = 'System Default'
DEFAULT_COMPANY_EMAIL = 'system@churnbuster.com'

def ensure_directories():
    """Create all required directories if they don't exist."""
    directories = [
        os.path.join(DATASETS_DIR, 'dev', 'uploadToRetrain'),
        os.path.join(DATASETS_DIR, 'dev', 'combinedDataset'),
        os.path.join(DATASETS_DIR, 'dev', 'uploadToPredict'),
        os.path.join(DATASETS_DIR, 'dev', 'predictionResult'),
        os.path.join(DATASETS_DIR, 'user', 'uploadToPredict'),
        os.path.join(DATASETS_DIR, 'user', 'predictionResult'),
        os.path.join(DATASETS_DIR, 'original'),
        RETRAINED_MODELS_DIR
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def initialize_system_company():
    """Initialize the system company if it doesn't exist.
    
    This is necessary because the database schema requires a valid company_id for models and datasets.
    The system company is a placeholder that owns the default models and original dataset.
    """
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if system company already exists
            result = conn.execute(text("""
                SELECT id FROM companies WHERE id = :company_id
            """), {'company_id': DEFAULT_COMPANY_ID})
            
            if not result.fetchone():
                # Insert the system company
                conn.execute(text("""
                    INSERT INTO companies (id, name, email, registration_date, email_verified)
                    VALUES (:id, :name, :email, CURRENT_TIMESTAMP, 1)
                """), {
                    'id': DEFAULT_COMPANY_ID,
                    'name': DEFAULT_COMPANY_NAME,
                    'email': DEFAULT_COMPANY_EMAIL
                })
                
                conn.commit()
                logger.info(f"Initialized system company with ID: {DEFAULT_COMPANY_ID}")
                return True
            else:
                logger.info(f"System company already exists with ID: {DEFAULT_COMPANY_ID}")
                return False
    
    except Exception as e:
        logger.error(f"Error initializing system company: {str(e)}")
        raise

def load_model_metadata(metadata_file):
    """Load model metadata from pkl file."""
    # Convert relative path to absolute for file operations
    absolute_path = os.path.abspath(metadata_file)
    
    try:
        with open(absolute_path, 'rb') as f:
            metadata = pickle.load(f)
            
            # Extract the model name from the file path
            model_name = os.path.basename(metadata_file).replace('_metadata.pkl', '')
            
            # Extract metrics from the metadata
            metrics = metadata.get('metrics', {})
            
            # Convert metrics keys to lowercase and standardize names
            standardized_metrics = {
                'accuracy': metrics.get('Accuracy', 0.0),
                'precision': metrics.get('Precision', 0.0),
                'recall': metrics.get('Recall', 0.0),
                'f1_score': metrics.get('F1 Score', 0.0),
                'auc': metrics.get('AUC', 0.0)
            }
            
            return {
                'name': model_name,
                'metrics': standardized_metrics,
                'raw_metadata': metadata
            }
    except Exception as e:
        logger.error(f"Error loading metadata from {metadata_file}: {str(e)}")
        raise

def register_model_types():
    """Register all model types in the modeltypes table if they don't exist."""
    model_types = [
        {'name': 'Neural Network', 'description': 'Artificial neural network model for classification'},
        {'name': 'Random Forest', 'description': 'Ensemble learning method using multiple decision trees'},
        {'name': 'Gradient Boosting', 'description': 'Ensemble technique that builds models sequentially to correct errors'},
        {'name': 'Logistic Regression', 'description': 'Statistical model that uses a logistic function for classification'},
        {'name': 'Decision Tree', 'description': 'Tree-like model of decisions for classification'}
    ]
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            for model_type in model_types:
                # Check if model type already exists
                result = conn.execute(text("""
                    SELECT id FROM modeltypes WHERE name = :name
                """), {'name': model_type['name']})
                
                if not result.fetchone():
                    # Insert the model type
                    conn.execute(text("""
                        INSERT INTO modeltypes (name, description)
                        VALUES (:name, :description)
                    """), model_type)
                    
                    conn.commit()
                    logger.info(f"Registered model type: {model_type['name']}")
                else:
                    logger.info(f"Model type {model_type['name']} already exists")
    
    except Exception as e:
        logger.error(f"Error registering model types: {str(e)}")
        raise

def get_model_type_id(model_name):
    """Get the model type ID from the database."""
    # Map model file names to their model type names
    model_type_mapping = {
        'neural_network': 'Neural Network',
        'random_forest': 'Random Forest',
        'gradient_boosting': 'Gradient Boosting',
        'logistic_regression': 'Logistic Regression',
        'decision_tree': 'Decision Tree'
    }
    
    # Get the model type name from the mapping
    model_type_name = model_type_mapping.get(model_name, model_name)
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id FROM modeltypes WHERE name = :name
            """), {'name': model_type_name})
            
            row = result.fetchone()
            
            if row:
                return row[0]
            else:
                raise ValueError(f"Model type '{model_type_name}' not found in the database")
    
    except Exception as e:
        logger.error(f"Error getting model type ID: {str(e)}")
        raise

def initialize_original_dataset():
    """Initialize the original dataset (DatasetA.csv) as a shared resource."""
    engine = create_engine(DATABASE_URL)
    
    try:
        # Check if the original dataset file exists (using absolute path for file check)
        if not os.path.exists(os.path.abspath(ORIGINAL_DATASET)):
            raise FileNotFoundError(f"Original dataset not found at {ORIGINAL_DATASET}")
        
        # Use relative path for database record
        dataset_path = ORIGINAL_DATASET
        
        with engine.connect() as conn:
            # Check if dataset already exists
            result = conn.execute(text("""
                SELECT id FROM datasets 
                WHERE company_id = :company_id AND is_original = 1
            """), {'company_id': DEFAULT_COMPANY_ID})
            
            if not result.fetchone():
                # Insert the dataset record
                conn.execute(text("""
                    INSERT INTO datasets (
                        company_id, name, file_path, 
                        is_original, is_uploaded, is_combined,
                        created_at
                    ) VALUES (
                        :company_id, :name, :path, 
                        1, 0, 0, CURRENT_TIMESTAMP
                    )
                """), {
                    'company_id': DEFAULT_COMPANY_ID,
                    'name': 'DatasetA',
                    'path': dataset_path
                })
                
                conn.commit()
                logger.info(f"Initialized original dataset: {dataset_path}")
                return True
            else:
                logger.info(f"Original dataset already exists")
                return False
    
    except Exception as e:
        logger.error(f"Error initializing original dataset: {str(e)}")
        raise

def register_default_models():
    """Register all default models in the database.
    
    These models will be shared resources available to all companies.
    They're linked to the system company to satisfy foreign key constraints.
    """
    engine = create_engine(DATABASE_URL)
    
    try:
        # Get all model files from the default models directory
        model_files = {}
        
        # Need to use absolute path for directory listing
        abs_default_models_dir = os.path.abspath(DEFAULT_MODELS_DIR)
        
        for file in os.listdir(abs_default_models_dir):
            if file.endswith('.pkl'):
                model_name = file.replace('.pkl', '')
                
                if not model_name.endswith('_metadata'):
                    metadata_file = f"{model_name}_metadata.pkl"
                    if os.path.exists(os.path.join(abs_default_models_dir, metadata_file)):
                        model_files[model_name] = {
                            'model': file,
                            'metadata': metadata_file
                        }
        
        # Register each model in the database
        for model_name, files in model_files.items():
            # Use relative paths for database records
            model_path = os.path.join(DEFAULT_MODELS_DIR, files['model'])
            metadata_path = os.path.join(DEFAULT_MODELS_DIR, files['metadata'])
            
            # Load the metadata - we pass the absolute path for loading the file
            metadata = load_model_metadata(os.path.join(abs_default_models_dir, files['metadata']))
            metrics = metadata['metrics']
            
            # Get the model type ID
            model_type_id = get_model_type_id(model_name)
            
            with engine.connect() as conn:
                # Check if the model already exists
                result = conn.execute(text("""
                    SELECT id FROM models 
                    WHERE company_id = :company_id AND model_type_id = :model_type_id AND version = '1'
                """), {
                    'company_id': DEFAULT_COMPANY_ID,
                    'model_type_id': model_type_id
                })
                
                if not result.fetchone():
                    # Insert the model record with relative path
                    conn.execute(text("""
                        INSERT INTO models (
                            model_type_id, name, version, file_path,
                            is_default, company_id, created_at, updated_at
                        ) VALUES (
                            :model_type_id, :name, '1', :path,
                            1, :company_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """), {
                        'model_type_id': model_type_id,
                        'name': model_name,
                        'path': model_path,
                        'company_id': DEFAULT_COMPANY_ID
                    })
                    
                    # Get the model ID
                    result = conn.execute(text("""
                        SELECT id FROM models 
                        WHERE company_id = :company_id AND model_type_id = :model_type_id AND version = '1'
                    """), {
                        'company_id': DEFAULT_COMPANY_ID,
                        'model_type_id': model_type_id
                    })
                    
                    model_id = result.fetchone()[0]
                    
                    # Insert the model metrics - Use backticks around 'precision' since it's a reserved keyword
                    conn.execute(text("""
                        INSERT INTO modelmetrics (
                            model_id, accuracy, `precision`, recall,
                            f1_score, auc_roc, additional_metrics, created_at
                        ) VALUES (
                            :model_id, :accuracy, :precision, :recall,
                            :f1_score, :auc_roc, :additional_metrics, CURRENT_TIMESTAMP
                        )
                    """), {
                        'model_id': model_id,
                        'accuracy': metrics['accuracy'],
                        'precision': metrics['precision'],
                        'recall': metrics['recall'],
                        'f1_score': metrics['f1_score'],
                        'auc_roc': metrics['auc'],
                        'additional_metrics': json.dumps(metadata['raw_metadata'])
                    })
                    
                    conn.commit()
                    logger.info(f"Registered default model {model_name}")
                else:
                    logger.info(f"Default model {model_name} already exists")
        
        return True
    
    except Exception as e:
        logger.error(f"Error registering default models: {str(e)}")
        raise

def initialize_system():
    """Initialize the system with default models and dataset.
    
    This is the main function that performs the complete system initialization.
    It needs to be run once before the application is used.
    """
    try:
        # Ensure all required directories exist
        ensure_directories()
        
        # Initialize system company (needed for foreign key constraints)
        initialize_system_company()
        
        # Register model types
        register_model_types()
        
        # Initialize the original dataset
        initialize_original_dataset()
        
        # Register default models
        register_default_models()
        
        logger.info(f"Successfully initialized system with default models and dataset")
        return {
            'status': 'success',
            'message': f"System initialized successfully with default models and dataset"
        }
    
    except Exception as e:
        logger.error(f"Error initializing system: {str(e)}")
        return {
            'status': 'error',
            'message': f"Error initializing system: {str(e)}"
        }

if __name__ == '__main__':
    # Initialize the system (only needs to be run once)
    result = initialize_system()
    print("System initialization result:", result) 