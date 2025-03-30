import os
import pickle
import pandas as pd
from datetime import datetime
import sqlite3
from sqlalchemy import create_engine, text
import json

# Database connection settings
DB_USER = 'root'
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_NAME = 'fyp_db'

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

def load_model_metadata(metadata_file):
    """Load model metadata from pickle file."""
    with open(metadata_file, 'rb') as f:
        metadata = pickle.load(f)
        # Extract metrics and standardize the keys
        metrics = metadata['metrics']
        return {
            'accuracy': metrics['Accuracy'],
            'precision': metrics['Precision'],
            'recall': metrics['Recall'],
            'f1_score': metrics['F1 Score'],
            'auc': metrics.get('AUC', None)  # Add AUC if available
        }

def register_model_in_db(developer_id, model_name, model_path, metadata_path, metrics):
    """Register model information in the database."""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if model already exists for this developer
            result = conn.execute(text("""
                SELECT id FROM Models 
                WHERE developer_id = :dev_id 
                AND model_name = :model_name 
                AND is_system_default = 1
            """), {
                'dev_id': developer_id,
                'model_name': model_name
            })
            
            existing_model = result.fetchone()
            
            if not existing_model:
                # Convert metadata to JSON string
                metadata_json = {
                    'metadata_path': metadata_path,
                    'model_type': model_name,
                    'metrics': {
                        'accuracy': metrics['accuracy'],
                        'precision': metrics['precision'],
                        'recall': metrics['recall'],
                        'f1_score': metrics['f1_score']
                    }
                }
                
                # Insert new model
                conn.execute(text("""
                    INSERT INTO Models (
                        developer_id, model_name, model_file_path, 
                        metadata, accuracy, precision_score, recall, 
                        f1_score, roc_auc, is_system_default, version, 
                        evaluation_type, created_at
                    ) VALUES (
                        :dev_id, :name, :path, 
                        :metadata, :accuracy, :precision, :recall,
                        :f1_score, :roc_auc, 1, 1, 'default', CURRENT_TIMESTAMP
                    )
                """), {
                    'dev_id': developer_id,
                    'name': model_name,
                    'path': model_path,
                    'metadata': json.dumps(metadata_json),  # Convert dict to JSON string
                    'accuracy': metrics['accuracy'],
                    'precision': metrics['precision'],
                    'recall': metrics['recall'],
                    'f1_score': metrics['f1_score'],
                    'roc_auc': metrics.get('auc', None)  # Add ROC AUC if available
                })
                
                conn.commit()
                print(f"Registered model {model_name} for developer {developer_id}")
            else:
                print(f"Model {model_name} already exists for developer {developer_id}")
                
    except Exception as e:
        print(f"Error registering model: {str(e)}")
        raise

def initialize_default_models(developer_id):
    """Initialize all default models and register them in the database."""
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
        model_path = os.path.abspath(os.path.join(models_dir, files['model']))
        metadata_path = os.path.abspath(os.path.join(models_dir, files['metadata']))
        
        try:
            # Load metadata
            metrics = load_model_metadata(metadata_path)
            
            # Register in database
            register_model_in_db(
                developer_id=developer_id,
                model_name=model_name,
                model_path=model_path,
                metadata_path=metadata_path,
                metrics=metrics
            )
            
            initialized_models.append({
                'name': model_name,
                'metrics': metrics
            })
            
        except Exception as e:
            print(f"Error initializing {model_name}: {str(e)}")
    
    return initialized_models

def get_model_metrics(developer_id):
    """Retrieve all model metrics from the database for a specific developer."""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    model_name, accuracy, precision_score, 
                    recall, f1_score, roc_auc,
                    EXISTS(
                        SELECT 1 FROM Deployments d 
                        WHERE d.model_id = Models.id 
                        AND d.is_active = 1
                    ) as is_deployed
                FROM Models
                WHERE developer_id = :dev_id
                AND is_system_default = 1
            """), {'dev_id': developer_id})
            
            metrics = []
            for row in result:
                metrics.append({
                    'name': row[0],
                    'accuracy': float(row[1]),
                    'precision': float(row[2]),
                    'recall': float(row[3]),
                    'f1_score': float(row[4]),
                    'roc_auc': float(row[5]) if row[5] is not None else None,
                    'is_deployed': bool(row[6])
                })
            
            return metrics
            
    except Exception as e:
        print(f"Error getting metrics: {str(e)}")
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

def initialize_developer_environment(developer_id):
    """Initialize the complete environment for a new developer."""
    try:
        # Initialize original dataset
        initialize_original_dataset(developer_id)
        
        # Initialize default models
        initialized_models = initialize_default_models(developer_id)
        
        return {
            'status': 'success',
            'message': 'Developer environment initialized successfully',
            'data': initialized_models
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error initializing developer environment: {str(e)}'
        }

if __name__ == '__main__':
    # Test initialization with a sample developer ID
    test_developer_id = 1
    result = initialize_developer_environment(test_developer_id)
    print("Initialization result:", result) 