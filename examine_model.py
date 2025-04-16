import pickle
import os
import sys

def examine_model(model_type):
    model_path = os.path.join('models', 'default_models', f"{model_type}.pkl")
    feature_path = os.path.join('models', 'default_models', f"{model_type}_features.pkl")
    
    print(f"Examining {model_type} model...")
    print(f"Model file exists: {os.path.exists(model_path)}")
    print(f"Features file exists: {os.path.exists(feature_path)}")
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        print(f"Model type: {type(model)}")
        print(f"Model attributes: {dir(model)}")
        
        # Check for feature importance attributes
        if hasattr(model, 'feature_importances_'):
            print("Has feature_importances_: Yes")
            print(f"feature_importances_ shape: {model.feature_importances_.shape}")
        else:
            print("Has feature_importances_: No")
            
        if hasattr(model, 'coef_'):
            print("Has coef_: Yes")
            print(f"coef_ shape: {model.coef_.shape}")
        else:
            print("Has coef_: No")
        
        # Load feature names
        if os.path.exists(feature_path):
            with open(feature_path, 'rb') as f:
                features = pickle.load(f)
            print(f"Number of features: {len(features)}")
            print(f"First 5 features: {features[:5]}")
        
    except Exception as e:
        print(f"Error examining model: {str(e)}")

if __name__ == "__main__":
    model_types = ["neural_network", "random_forest", "gradient_boosting", "logistic_regression", "decision_tree"]
    
    if len(sys.argv) > 1 and sys.argv[1] in model_types:
        examine_model(sys.argv[1])
    else:
        for model_type in model_types:
            examine_model(model_type)
            print("-" * 50)
