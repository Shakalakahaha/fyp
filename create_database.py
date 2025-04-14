import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
import logging
import argparse

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

def drop_database():
    """Drop the database if it exists."""
    try:
        # Connect to MySQL without specifying a database
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}")
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{DB_NAME}'"))
            
            if result.fetchone():
                # Drop the database
                conn.execute(text(f"DROP DATABASE {DB_NAME}"))
                conn.commit()
                logger.info(f"Database '{DB_NAME}' has been dropped.")
            else:
                logger.info(f"Database '{DB_NAME}' does not exist. Nothing to drop.")
                
    except Exception as e:
        logger.error(f"An error occurred while dropping the database: {str(e)}")
        raise

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to MySQL without specifying a database
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}")
        
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
            conn.commit()
            logger.info(f"Database '{DB_NAME}' created or already exists")
            
    except Exception as e:
        logger.error(f"An error occurred while creating the database: {str(e)}")
        raise

def create_tables():
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()

        # 1. Companies Table
        companies = Table('companies', metadata,
            Column('id', String(10), primary_key=True),
            Column('name', String(255), nullable=False),
            Column('email', String(255), unique=True, nullable=False),
            Column('registration_date', DateTime, server_default=func.current_timestamp()),
            Column('email_verified', Boolean, server_default='0')
        )

        # 2. Developers Table
        developers = Table('developers', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('company_id', String(10), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
            Column('email', String(255), unique=True, nullable=False),
            Column('password_hash', String(255), nullable=False),
            Column('registration_date', DateTime, server_default=func.current_timestamp()),
            Column('email_verified', Boolean, server_default='0'),
            UniqueConstraint('company_id', name='unique_company_developer')
        )

        # 3. Users Table
        users = Table('users', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('company_id', String(10), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
            Column('email', String(255), unique=True, nullable=False),
            Column('password_hash', String(255), nullable=False),
            Column('registration_date', DateTime, server_default=func.current_timestamp()),
            Column('email_verified', Boolean, server_default='0')
        )

        # 4. Model Types Table
        modeltypes = Table('modeltypes', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('name', String(255), unique=True, nullable=False),
            Column('description', Text)
        )

        # 5. Datasets Table
        datasets = Table('datasets', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('company_id', String(10), ForeignKey('companies.id', ondelete='CASCADE')),
            Column('name', String(255), nullable=False),
            Column('file_path', String(255), nullable=False),
            Column('is_original', Boolean),
            Column('is_uploaded', Boolean),
            Column('is_combined', Boolean),
            Column('parent_dataset_id', Integer, ForeignKey('datasets.id')),
            Column('created_at', DateTime, server_default=func.current_timestamp())
        )

        # 6. Models Table
        models = Table('models', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('model_type_id', Integer, ForeignKey('modeltypes.id'), nullable=False),
            Column('name', String(255), nullable=False),
            Column('version', String(10), nullable=False),
            Column('file_path', String(255), nullable=False),
            Column('is_default', Boolean),
            Column('company_id', String(10), ForeignKey('companies.id', ondelete='CASCADE')),
            Column('training_dataset_id', Integer, ForeignKey('datasets.id')),
            Column('created_at', DateTime, server_default=func.current_timestamp()),
            Column('updated_at', DateTime, server_default=func.current_timestamp()),
            UniqueConstraint('model_type_id', 'version', 'company_id', name='unique_model_version_company')
        )

        # 7. Model Metrics Table
        modelmetrics = Table('modelmetrics', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('model_id', Integer, ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
            Column('accuracy', Float),
            Column('precision', Float),
            Column('recall', Float),
            Column('f1_score', Float),
            Column('auc_roc', Float),
            Column('additional_metrics', JSON),
            Column('created_at', DateTime, server_default=func.current_timestamp())
        )

        # 8. Model Deployments Table
        modeldeployments = Table('modeldeployments', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('company_id', String(10), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
            Column('model_id', Integer, ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
            Column('deployed_by', Integer, ForeignKey('developers.id', ondelete='CASCADE')),
            Column('is_active', Boolean),
            Column('deployed_at', DateTime, server_default=func.current_timestamp()),
            Column('deactivated_at', DateTime)
        )

        # 9. Predictions Table
        predictions = Table('predictions', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
            Column('developer_id', Integer, ForeignKey('developers.id', ondelete='CASCADE')),
            Column('model_id', Integer, ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
            Column('prediction_name', String(255), nullable=False),
            Column('input_data', JSON),
            Column('result', JSON),
            Column('upload_dataset_path', String(255)),
            Column('result_dataset_path', String(255)),
            Column('created_at', DateTime, server_default=func.current_timestamp())
        )

        # Create all tables
        metadata.create_all(engine)
        logger.info("All tables created successfully!")

    except SQLAlchemyError as e:
        logger.error(f"An error occurred while creating tables: {str(e)}")
        raise

def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Setup the database for the project.')
        parser.add_argument('--reset', action='store_true', help='Reset the database by dropping and recreating it')
        args = parser.parse_args()
        
        if args.reset:
            # Drop database if it exists
            logger.info("Resetting database...")
            drop_database()
        
        # Create database
        create_database()
        
        # Create tables
        create_tables()
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred during database setup: {str(e)}")
        raise

if __name__ == "__main__":
    main() 