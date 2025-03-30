import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, Enum, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection settings
DB_USER = 'root'  # Replace with your MySQL username
DB_PASSWORD = ''  # Replace with your MySQL password
DB_HOST = 'localhost'
DB_NAME = 'fyp_db'  # Replace with your desired database name

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

def create_tables():
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()

        # 1. Companies Table
        companies = Table('Companies', metadata,
            Column('id', String(10), primary_key=True),
            Column('name', String(255), nullable=False),
            Column('email', String(255), unique=True, nullable=False),
            Column('registration_date', DateTime, server_default=func.current_timestamp()),
            Column('email_verified', Boolean, server_default='0')
        )

        # 2. Developers Table
        developers = Table('Developers', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('company_id', String(10), ForeignKey('Companies.id', ondelete='CASCADE'), nullable=False),
            Column('email', String(255), unique=True, nullable=False),
            Column('password_hash', String(255), nullable=False),
            Column('registration_date', DateTime, server_default=func.current_timestamp()),
            Column('email_verified', Boolean, server_default='0'),
            UniqueConstraint('company_id', name='unique_company_developer')
        )

        # 3. Users Table
        users = Table('Users', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('company_id', String(10), ForeignKey('Companies.id', ondelete='CASCADE'), nullable=False),
            Column('email', String(255), unique=True, nullable=False),
            Column('password_hash', String(255), nullable=False),
            Column('registration_date', DateTime, server_default=func.current_timestamp()),
            Column('email_verified', Boolean, server_default='0')
        )

        # 4. Datasets Table
        datasets = Table('Datasets', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('developer_id', Integer, ForeignKey('Developers.id', ondelete='CASCADE'), nullable=False),
            Column('dataset_name', String(255), nullable=False),
            Column('file_path', String(255), nullable=False),
            Column('row_count', Integer),
            Column('is_system_default', Boolean, server_default='0'),
            Column('created_at', DateTime, server_default=func.current_timestamp()),
            Index('idx_developer_dataset', 'developer_id')
        )

        # 5. Dataset Combinations Table
        dataset_combinations = Table('Dataset_Combinations', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('new_dataset_id', Integer, ForeignKey('Datasets.id', ondelete='CASCADE'), nullable=False),
            Column('parent_dataset1_id', Integer, ForeignKey('Datasets.id', ondelete='CASCADE'), nullable=False),
            Column('parent_dataset2_id', Integer, ForeignKey('Datasets.id', ondelete='CASCADE'), nullable=False),
            Column('created_at', DateTime, server_default=func.current_timestamp()),
            Index('idx_new_dataset', 'new_dataset_id')
        )

        # 6. Models Table
        models = Table('Models', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('developer_id', Integer, ForeignKey('Developers.id', ondelete='CASCADE'), nullable=False),
            Column('model_name', String(255), nullable=False),
            Column('parent_model_id', Integer, ForeignKey('Models.id', ondelete='SET NULL')),
            Column('evaluation_type', Enum('default', 're-evaluated', 'retrained'), server_default='default', nullable=False),
            Column('accuracy', Float, nullable=False),
            Column('precision_score', Float, nullable=False),
            Column('recall', Float, nullable=False),
            Column('f1_score', Float, nullable=False),
            Column('roc_auc', Float),
            Column('model_file_path', String(255), nullable=False),
            Column('metadata', JSON),
            Column('is_system_default', Boolean, server_default='0'),
            Column('version', Integer, nullable=False, server_default='1'),
            Column('deployment_count', Integer, nullable=False, server_default='0'),
            Column('created_at', DateTime, server_default=func.current_timestamp()),
            Index('idx_developer_model', 'developer_id'),
            Index('idx_model_metrics', 'accuracy', 'f1_score'),
            Index('idx_model_versioning', 'developer_id', 'model_name', 'version')
        )

        # 7. Training Sessions Table
        training_sessions = Table('Training_Sessions', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('developer_id', Integer, ForeignKey('Developers.id', ondelete='CASCADE'), nullable=False),
            Column('dataset_id', Integer, ForeignKey('Datasets.id', ondelete='CASCADE'), nullable=False),
            Column('original_model_id', Integer, ForeignKey('Models.id', ondelete='CASCADE'), nullable=False),
            Column('new_model_id', Integer, ForeignKey('Models.id', ondelete='SET NULL')),
            Column('training_status', Enum('pending', 'in_progress', 'completed', 'failed'), server_default='pending'),
            Column('error_message', Text),
            Column('started_at', DateTime, server_default=func.current_timestamp()),
            Column('completed_at', DateTime),
            Index('idx_training_developer', 'developer_id'),
            Index('idx_training_status', 'training_status')
        )

        # 8. Retraining History Table
        retraining_history = Table('Retraining_History', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('training_session_id', Integer, ForeignKey('Training_Sessions.id', ondelete='CASCADE'), nullable=False),
            Column('developer_id', Integer, ForeignKey('Developers.id', ondelete='CASCADE'), nullable=False),
            Column('original_model_id', Integer, ForeignKey('Models.id', ondelete='CASCADE'), nullable=False),
            Column('retrained_model_id', Integer, ForeignKey('Models.id', ondelete='CASCADE'), nullable=False),
            Column('dataset_id', Integer, ForeignKey('Datasets.id', ondelete='CASCADE'), nullable=False),
            Column('old_accuracy', Float, nullable=False),
            Column('new_accuracy', Float, nullable=False),
            Column('old_precision', Float, nullable=False),
            Column('new_precision', Float, nullable=False),
            Column('old_recall', Float, nullable=False),
            Column('new_recall', Float, nullable=False),
            Column('old_f1_score', Float, nullable=False),
            Column('new_f1_score', Float, nullable=False),
            Column('old_roc_auc', Float),
            Column('new_roc_auc', Float),
            Column('created_at', DateTime, server_default=func.current_timestamp()),
            Index('idx_retraining_developer', 'developer_id')
        )

        # 9. Deployments Table
        deployments = Table('Deployments', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('company_id', String(10), ForeignKey('Companies.id', ondelete='CASCADE'), nullable=False),
            Column('model_id', Integer, ForeignKey('Models.id', ondelete='CASCADE'), nullable=False),
            Column('deployed_by', Integer, ForeignKey('Developers.id', ondelete='CASCADE'), nullable=False),
            Column('is_active', Boolean, server_default='1'),
            Column('deployed_at', DateTime, server_default=func.current_timestamp()),
            Column('undeployed_at', DateTime),
            Index('idx_company_deployment', 'company_id', 'is_active'),
            Index('idx_company_model_active', 'company_id', 'model_id', 'is_active'),
            UniqueConstraint('company_id', 'is_active', name='unique_active_deployment')
        )

        # 10. Predictions Table
        predictions = Table('Predictions', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('user_id', Integer, ForeignKey('Users.id', ondelete='SET NULL')),
            Column('developer_id', Integer, ForeignKey('Developers.id', ondelete='SET NULL')),
            Column('company_id', String(10), ForeignKey('Companies.id', ondelete='CASCADE'), nullable=False),
            Column('model_id', Integer, ForeignKey('Models.id', ondelete='CASCADE'), nullable=False),
            Column('dataset_id', Integer, ForeignKey('Datasets.id', ondelete='SET NULL')),
            Column('input_data', JSON, nullable=False),
            Column('prediction_result', JSON, nullable=False),
            Column('record_count', Integer, nullable=False, server_default='1'),
            Column('created_at', DateTime, server_default=func.current_timestamp()),
            Column('status', Enum('active', 'archived'), server_default='active'),
            Index('idx_prediction_company', 'company_id'),
            Index('idx_prediction_created', 'created_at'),
            Index('idx_prediction_status', 'status')
        )

        # Create all tables
        metadata.create_all(engine)
        logger.info("All tables created successfully!")

    except SQLAlchemyError as e:
        logger.error(f"An error occurred while creating tables: {str(e)}")
        raise

def main():
    try:
        # Create database if it doesn't exist
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}")
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
            conn.commit()
            logger.info(f"Database '{DB_NAME}' created or already exists")

        # Create tables
        create_tables()

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 