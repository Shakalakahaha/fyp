# Churn Buster

A web-based customer churn prediction platform built with Flask, designed to help companies predict and reduce customer churn using machine learning models.

## Project Overview

Churn Buster is a machine learning application that helps companies predict customer churn using various prediction models. The system supports multiple user roles with different capabilities:

- **Companies**: Each company has a unique ID and can have one developer and multiple users
- **Developers**: Can retrain and deploy machine learning models
- **Users**: Can run predictions using available models

## System Architecture

### User Roles and Authentication
- **Company Registration**: Companies register with a name and email to receive a unique company ID
- **Developer Registration**: One developer per company registers using the company ID
- **User Registration**: Multiple users per company register using the company ID
- **Authentication Flow**: Secure login system with password hashing and email verification

### Model Management System
- **Default Models**: 5 pre-trained machine learning models stored in `models/default_models/`
- **Model Types**:
  - Gradient Boosting Machine (GBM) (highest accuracy among default models)
  - Random Forest
  - Neural Network
  - Logistic Regression
  - Decision Tree
- **Model Versioning**: System tracks versions of retrained models (v2, v3, etc.)
- **Model Deployment**: Developers can deploy new model versions to users of their company
- **Feature Importance**: All models provide normalized feature importance values (sum to 1.0) for the top 5 features

### Data Management System
- **Dataset Storage Structure**:
  - Original dataset: Initialized for all developers
  - Developer upload datasets: Stored in `datasets/dev/uploadToRetrain/`
  - Combined datasets: Stored in `datasets/dev/combinedDataset/`
  - Prediction datasets: Stored in `datasets/dev/uploadToPredict/` (developer) and `datasets/user/uploadToPredict/` (user)
  - Prediction results: Stored in `datasets/dev/predictionResult/` (developer) and `datasets/user/predictionResult/` (user)

### Database Schema
The system uses a relational database with the following tables:
- `companies`: Stores company information
- `developers`: Stores developer accounts (one per company)
- `users`: Stores user accounts (multiple per company)
- `modeltypes`: Catalogs the types of ML models available
- `datasets`: Tracks all datasets in the system
- `models`: Stores model information including version and file path
- `modelmetrics`: Records performance metrics for models
- `modeldeployments`: Tracks which models are deployed to which companies
- `predictions`: Records prediction operations performed by users and developers

## Initialization Process

The initialization process is managed by the `model_initialization.py` script, which sets up the necessary environment for each new developer. This includes:

### Default Model Initialization
- Five pre-trained machine learning models are included in the system:
  - Decision Tree (`decision_tree.pkl` and `decision_tree_metadata.pkl`)
  - Gradient Boosting (`gradient_boosting.pkl` and `gradient_boosting_metadata.pkl`)
  - Logistic Regression (`logistic_regression.pkl` and `logistic_regression_metadata.pkl`)
  - Random Forest (`random_forest.pkl` and `random_forest_metadata.pkl`)
  - Neural Network (`neural_network.pkl` and `neural_network_metadata.pkl`)

### Initialization Flow
1. **Load Model Metadata**: The system reads the metadata.pkl files to extract performance metrics for each model
2. **Register Models in Database**: Each model is registered in the database with:
   - Model type and name
   - File path to the model
   - Performance metrics (accuracy, precision, recall, F1 score, AUC)
   - Version information
   - Default status flag

3. **Initialize Original Dataset**: The system copies the original dataset (DatasetA.csv) and registers it in the database for the developer

4. **Create Directory Structure**: The system ensures all required directories exist:
   ```
   - datasets/
     - dev/
       - combinedDataset/
       - predictionResult/
       - uploadToPredict/
       - uploadToRetrain/
     - user/
       - predictionResult/
       - uploadToPredict/
   - models/
     - default_models/
       - decision_tree.pkl
       - decision_tree_metadata.pkl
       - gradient_boosting.pkl
       - gradient_boosting_metadata.pkl
       - logistic_regression.pkl
       - logistic_regression_metadata.pkl
       - neural_network.pkl
       - neural_network_metadata.pkl
       - random_forest.pkl
       - random_forest_metadata.pkl
     - retrained_models/
   ```

### Key Functions
- `load_model_metadata()`: Loads metrics from metadata files
- `check_existing_models()`: Verifies if a developer already has models initialized
- `register_model_in_db()`: Records model information in the database
- `initialize_default_models()`: Loads all default models and their metrics
- `get_model_metrics()`: Retrieves model performance data for a developer
- `initialize_original_dataset()`: Sets up the initial dataset for a developer
- `initialize_developer_environment()`: Main function that orchestrates the full initialization process

### Metadata Format
Each model's metadata is stored in a standardized format:
```python
{
    'model_type': 'Model Name',
    'metrics': {
        'Accuracy': 0.8096348096348096,
        'AUC': 0.850327660103112,
        'Precision': 0.8008413413551754,
        'Recall': 0.8096348096348096,
        'F1 Score': 0.8027330375218171
    }
}
```

### Database Integration
During initialization, the system:
1. Creates records in the `Models` table for each default model
2. Creates a record in the `Datasets` table for the original dataset
3. Records detailed metrics in the database for future comparison and tracking
4. Sets deployment status for all default models

## Implemented Features

### Authentication Module (Completed)
- Company registration and verification
- Developer account creation and management
- User account creation and management
- Secure login with password hashing

### Developer Functionality

#### Model Initialization
- System automatically initializes 5 default models for each developer
- Each model includes:
  - Model file (`.pkl`) for predictions
  - Metadata file (`.metadata.pkl`) with performance metrics
- Metrics format:
```python
{
    'model_type': 'Gradient Boosting',
    'metrics': {
        'Accuracy': 0.8096348096348096,
        'Precision': 0.8008413413551754,
        'Recall': 0.8096348096348096,
        'F1 Score': 0.8027330375218171
    }
}
```

#### Model Retraining
- Gradient Boosting Machine (GBM) retraining with custom datasets
- Dataset combination workflow:
  1. Developer uploads custom dataset
  2. System combines with existing dataset
  3. For subsequent retrains, combines with the most recent combined dataset
- Retraining parameters:
  - n_estimators: 400
  - learning_rate: 0.01
  - max_depth: 5
  - min_samples_split: 2
  - subsample: 0.8
  - Train/test split: 80/20

#### Model Deployment
- Deploy retrained models to company users
- Multiple version management
- Active/inactive deployment status tracking
- Toggle deployment status for retrained models

#### Prediction System
- Upload data for prediction (CSV or Excel format)
- Choose from available models (default or deployed)
- View and store prediction results
- Visualize prediction outcomes and feature importance
- Preview first 10 rows of prediction results
- Download original dataset and prediction results

##### Data Handling Requirements
- The system handles case sensitivity in column names
- Required columns for prediction models:
  - Categorical features: InternetService, OnlineSecurity, TechSupport, Contract, SeniorCitizen, Partner, Dependents, OnlineBackup, DeviceProtection, StreamingTV, StreamingMovies, PaymentMethod, PaperlessBilling
  - Numerical features: tenure, TotalCharges, MonthlyCharges
  - Meta: customerID
- Extra columns in uploaded datasets are preserved in results
- Churn column is not required for prediction (it's what we're predicting)

##### Prediction Output
- Visualization of churn distribution (predicted churn vs. non-churn)
- Visualization of feature importance (top 5 features with normalized values)
- Preview of first 10 rows of prediction results
- Downloadable result file containing original data plus prediction columns (Churn_Prediction and Churn_Probability)

##### Prediction History
- View history of all predictions made
- Filter and search prediction history
- For each prediction: view results, download original dataset, download prediction results

### User Functionality

#### Model Access
- Access to 5 default models by default
- Access to developer-deployed models when available for their company

#### Prediction Workflow
1. Create prediction name
2. Select a model (default or developer-deployed)
3. Upload dataset for prediction (CSV or Excel)
4. View visualizations and download prediction results
5. Access prediction history with options to view results, download original dataset, and download prediction results

#### User Dashboard
- Clean, intuitive interface for making predictions
- Prediction history section with detailed results
- Ability to view feature importance and churn distribution for past predictions

## Database Integration

### Model Storage and Retrieval
- Models stored as PKL files with standardized naming conventions
- Model metadata stored separately for quick access to performance metrics
- Database records link to file locations on the server

### Dataset Management
- Original datasets provided during initialization
- Tracking of dataset lineage (parent-child relationships)
- Versioned storage of combined datasets

### Prediction History
- Complete record of all predictions made
- Links to input data and prediction results
- Filter by user, model, and date

## Implementation Status
- Authentication system: ✅ Complete
- Database schema: ✅ Complete
- Model initialization: ✅ Complete
- Retraining functionality: ✅ Complete
- Prediction system: ✅ Complete
- Model deployment: ✅ Complete
- Feature importance calculation: ✅ Complete
- Prediction history: ✅ Complete
- Developer dashboard: ✅ Complete
- User dashboard: ✅ Complete
- FAQ section: ✅ Complete

## Technical Details

### File Structure
```
project/
├── app/
│   ├── models/
│   │   ├── default_models/       # 5 pre-trained default models
│   │   └── retrained_models/     # Developer retrained models
│   ├── datasets/
│   │   ├── dev/
│   │   │   ├── uploadToRetrain/  # Developer uploaded datasets for retraining
│   │   │   ├── combinedDataset/  # Combined datasets for training
│   │   │   ├── uploadToPredict/  # Developer uploaded datasets for prediction
│   │   │   └── predictionResult/ # Developer prediction results
│   │   └── user/
│   │       ├── uploadToPredict/  # User uploaded datasets for prediction
│   │       └── predictionResult/ # User prediction results
│   ├── templates/                # HTML templates
│   ├── static/                   # CSS, JS and image files
│   └── routes/                   # Application routes
├── create_database.py            # Database initialization script
├── model_initialization.py       # Model and developer environment initialization
├── DatasetA.csv                  # Original dataset used for initialization
└── README.md                     # Project documentation
```

### Gradient Boosting Machine (GBM) Retraining Process
1. Load existing GBM model parameters
2. Combine new dataset with previous combined dataset
3. Preprocess data (encoding categorical variables, scaling)
4. Split data (80% training, 20% testing)
5. Train model with specified parameters (n_estimators: 400, learning_rate: 0.01, max_depth: 5)
6. Evaluate model performance
7. Compare metrics with previous model version
8. Save model and performance metrics
9. Update database with new model information

### Feature Importance Calculation
1. For tree-based models (GBM, Random Forest, Decision Tree): Use built-in feature_importances_
2. For linear models (Logistic Regression): Use absolute values of coefficients
3. For Neural Networks: Calculate importance based on weights in the first layer
4. Normalize all importance values to sum to 1.0
5. Return top 5 features by importance

### Dashboard Features
1. **Developer Dashboard**:
   - Quick actions for retraining and prediction
   - Available models table with metrics
   - Model management with deployment controls
   - Prediction system with visualizations
   - Retraining interface with performance comparison
   - Prediction history with detailed results
   - FAQ section with system information

2. **User Dashboard**:
   - Simplified interface for predictions
   - Access to deployed models
   - Visualization of prediction results
   - Prediction history with result viewing

