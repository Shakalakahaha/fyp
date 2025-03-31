import os
import pickle
import pandas as pd
from datetime import datetime
import sqlite3
from sqlalchemy import create_engine, text
import json
import logging

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

def load_model_metadata(metadata_file):
    """Load model metadata directly from pickle file."""
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
            # Return the metrics exactly as they are in the metadata file
            return {
                'name': os.path.basename(metadata_file).replace('_metadata.pkl', ''),
                'metrics': metadata['metrics']
            }
    except Exception as e:
        logger.error(f"Error loading metadata from {metadata_file}: {str(e)}")
        raise

def check_existing_models(developer_id, engine):
    """Check if developer has any existing models."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT model_name, version FROM Models 
                WHERE developer_id = :dev_id
            """), {'dev_id': developer_id})
            return {row[0]: row[1] for row in result}
    except Exception as e:
        logger.error(f"Error checking existing models: {str(e)}")
        raise

def register_model_in_db(developer_id, model_name, model_path, metadata_path, metrics, version=1):
    """Register model information in the database."""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Convert metadata to JSON string
            metadata_json = {
                'metadata_path': metadata_path,
                'model_type': model_name,
                'metrics': {
                    'accuracy': metrics['accuracy'],
                    'precision': metrics['precision'],
                    'recall': metrics['recall'],
                    'f1_score': metrics['f1_score'],
                    'auc': metrics.get('auc', None)
                }
            }
            
            # Insert new model version
            conn.execute(text("""
                INSERT INTO Models (
                    developer_id, model_name, model_file_path, 
                    metadata, accuracy, precision_score, recall, 
                    f1_score, roc_auc, is_system_default, version, 
                    evaluation_type, created_at
                ) VALUES (
                    :dev_id, :name, :path, 
                    :metadata, :accuracy, :precision, :recall,
                    :f1_score, :roc_auc, 1, :version, 'default', CURRENT_TIMESTAMP
                )
            """), {
                'dev_id': developer_id,
                'name': model_name,
                'path': model_path,
                'metadata': json.dumps(metadata_json),
                'accuracy': metrics['accuracy'],
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1_score': metrics['f1_score'],
                'roc_auc': metrics.get('auc', None),
                'version': version
            })
            
            conn.commit()
            logger.info(f"Registered model {model_name} (v{version}) for developer {developer_id}")
                
    except Exception as e:
        logger.error(f"Error registering model: {str(e)}")
        raise

def initialize_default_models():
    """Load all default models and their metrics directly from files."""
    models_dir = 'default_models'
    model_files = {
        'decision_tree': {
            'model': 'decision_tree.pkl',
            'metadata': 'decision_tree_metadata.pkl'
        },
        'gradient_boosting': {
            'model': 'gradient_boosting.pkl',
            'metadata': 'gradient_boosting_metadata.pkl'
        },
        'logistic_regression': {
            'model': 'logistic_regression.pkl',
            'metadata': 'logistic_regression_metadata.pkl'
        },
        'random_forest': {
            'model': 'random_forest.pkl',
            'metadata': 'random_forest_metadata.pkl'
        },
        'neural_network': {
            'model': 'neural_network.pkl',
            'metadata': 'neural_network_metadata.pkl'
        }
    }
    
    initialized_models = []
    
    for model_name, files in model_files.items():
        try:
            metadata_path = os.path.abspath(os.path.join(models_dir, files['metadata']))
            model_data = load_model_metadata(metadata_path)
            
            initialized_models.append({
                'name': model_name,
                'metrics': model_data['metrics'],
                'is_deployed': False  # Default models start as not deployed
            })
            
            logger.info(f"Loaded model {model_name} with metrics: {model_data['metrics']}")
            
        except Exception as e:
            logger.error(f"Error initializing {model_name}: {str(e)}")
            continue
    
    return initialized_models

def get_model_metrics(developer_id):
    """Retrieve all model metrics from the database for a specific developer."""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    model_name, version, accuracy, precision_score, 
                    recall, f1_score, roc_auc, metadata,
                    EXISTS(
                        SELECT 1 FROM Deployments d 
                        WHERE d.model_id = Models.id 
                        AND d.is_active = 1
                    ) as is_deployed
                FROM Models
                WHERE developer_id = :dev_id
                ORDER BY model_name, version DESC
            """), {'dev_id': developer_id})
            
            metrics = []
            for row in result:
                metrics.append({
                    'name': row[0],
                    'version': row[1],
                    'accuracy': float(row[2]),
                    'precision': float(row[3]),
                    'recall': float(row[4]),
                    'f1_score': float(row[5]),
                    'roc_auc': float(row[6]) if row[6] is not None else None,
                    'metadata': json.loads(row[7]),
                    'is_deployed': bool(row[8])
                })
            
            return metrics
            
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise

def initialize_original_dataset(developer_id):
    """Initialize the original dataset (DatasetA.csv) for a developer."""
    engine = create_engine(DATABASE_URL)
    
    dataset_path = os.path.abspath('DatasetA.csv')
    
    try:
        # Count rows in the dataset
        df = pd.read_csv(dataset_path)
        row_count = len(df)
        
        with engine.connect() as conn:
            # Check if developer already has the default dataset
            result = conn.execute(text("""
                SELECT id FROM Datasets 
                WHERE developer_id = :dev_id AND is_system_default = 1
            """), {'dev_id': developer_id})
            
            existing_dataset = result.fetchone()
            
            if not existing_dataset:
                # Insert the original dataset for this developer
                conn.execute(text("""
                    INSERT INTO Datasets (
                        developer_id, dataset_name, file_path, 
                        row_count, is_system_default, created_at
                    ) VALUES (
                        :dev_id, :name, :path, 
                        :rows, 1, CURRENT_TIMESTAMP
                    )
                """), {
                    'dev_id': developer_id,
                    'name': 'DatasetA',
                    'path': dataset_path,
                    'rows': row_count
                })
                
                conn.commit()
                print(f"Successfully initialized original dataset for developer {developer_id} with {row_count} rows")
            else:
                print(f"Developer {developer_id} already has the default dataset initialized")
        
    except Exception as e:
        print(f"Error initializing original dataset: {str(e)}")
        raise

def initialize_developer_environment():
    """Initialize the complete environment with default models."""
    try:
        # Initialize default models
        initialized_models = initialize_default_models()
        
        return {
            'status': 'success',
            'message': 'Developer environment initialized successfully',
            'data': initialized_models
        }
    except Exception as e:
        logger.error(f"Error initializing developer environment: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error initializing developer environment: {str(e)}'
        }

if __name__ == '__main__':
    # Test initialization with a sample developer ID
    test_developer_id = 1
    result = initialize_developer_environment()
    print("Initialization result:", result) 