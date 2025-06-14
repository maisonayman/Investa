import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.http import MediaIoBaseUpload
from firebase_admin import auth, db
import uuid
import os
import sys
import warnings
import logging
from typing import Dict, List, Union, Any, Optional, Tuple
import pandas as pd
import numpy as np
import joblib
from pathlib import Path


drive_service = build(
    'drive', 'v3', credentials=settings.GOOGLE_CREDENTIALS
)

# Temporary OTP storage (use a database in production)

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def send_otp_email(email):
    """Send OTP and store it temporarily in cache"""
    otp = generate_otp()
    
    subject = "Your OTP for Email Verification"
    message = f"Your OTP code is {otp}. It is valid for 5 minutes."
    sender = settings.EMAIL_HOST_USER
    recipient = [email]

    send_mail(subject, message, sender, recipient)

    # Store OTP in cache for 5 minutes
    cache.set(email, otp, timeout=300)


def send_password_reset_email_custom(email):
    try:
        action_code_settings = auth.ActionCodeSettings(
            url="https://ff5d-37-19-208-83.ngrok-free.app/reset-password/",  # هنا حطي رابط الفرونت أو flutter لو mobile
            handle_code_in_app=True
        )

        link = auth.generate_password_reset_link(email, action_code_settings)

        subject = "Reset Your Password"
        message = f"Click the link below to reset your password:\n\n{link}"
        sender = "no-reply@investa812.web.app"
        recipient = [email]

        send_mail(subject, message, sender, recipient)
        return True

    except Exception as e:
        raise Exception(f"Error sending password reset email: {e}")


def upload_video_to_drive(file_path, file_name, folder_id):
    try:

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]  # Now dynamic
        }
        media = MediaFileUpload(file_path, mimetype='video/mp4')

        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        drive_service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return f"https://drive.google.com/uc?id={file['id']}"

    except Exception as e:
        raise Exception(f"Google Drive upload failed: {str(e)}")


def upload_image_to_drive(file_obj, file_name, folder_id):

  
    try:
        service = build("drive", "v3", credentials=settings.GOOGLE_CREDENTIALS)

        file_stream = io.BytesIO(file_obj.read())
        media = MediaIoBaseUpload(file_stream, mimetype="image/jpeg", resumable=True)

        file_metadata = {
            "name": file_name,
            "parents": [folder_id]
        }

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        return f"https://drive.google.com/uc?id={uploaded_file['id']}"

    except Exception as e:
        raise Exception(f"Error uploading image to Google Drive: {e}")


def upload_file_to_drive(uploaded_file, file_name):
    """
    Accepts an uploaded file (Django InMemoryUploadedFile or TemporaryUploadedFile),
    saves it temporarily, uploads it to Google Drive, and returns the public URL.
    """
    try:
        # Save the uploaded file temporarily
        temp_filename = f"/tmp/{uuid.uuid4()}_{file_name}"
        with open(temp_filename, 'wb+') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Prepare metadata and upload to Drive
        file_metadata = {
            "name": file_name,
            "parents": [settings.FOLDER_ID_FOR_FILES]
        }
        media = MediaFileUpload(temp_filename, resumable=True)
        uploaded_file_metadata = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        # Make file public
        file_id = uploaded_file_metadata.get("id")
        drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        # Clean up temp file
        os.remove(temp_filename)

        return f"https://drive.google.com/uc?id={file_id}"

    except Exception as e:
        print(f"Error uploading file: {e}")
        return ""


def send_password_reset_email_custom(email):
    try:
        action_code_settings = auth.ActionCodeSettings(
            url="https://1ae0-102-190-139-157.ngrok-free.app/reset-password/",  # هنا حطي رابط الفرونت أو flutter لو mobile
            handle_code_in_app=True
        )

        link = auth.generate_password_reset_link(email, action_code_settings)

        subject = "Reset Your Password"
        message = f"Click the link below to reset your password:\n\n{link}"
        sender = "no-reply@investa812.web.app"
        recipient = [email]

        send_mail(subject, message, sender, recipient)
        return True

    except Exception as e:
        raise Exception(f"Error sending password reset email: {e}")


def get_or_create_drive_folder(folder_name, parent_folder_id):
    query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{folder_name}' and '{parent_folder_id}' in parents"
    results = drive_service.files().list(q=query, spaces='drive',
                                         fields='files(id, name)').execute()
    folders = results.get('files', [])

    if folders:
        # Folder exists, return the first one found
        return folders[0]['id']
    else:
        # Create new folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata,
        fields='id').execute()
        return folder.get('id')


def get_founder_projects(user_id):
    projects_ref = db.reference('projects')
    all_projects = projects_ref.get() or {} # Use a more descriptive name

    founder_projects_list = []
    # Iterate through items to get both the Firebase key (project_id) and the project data
    for project_id, project_data in all_projects.items():
        if project_data.get('user_id', '').strip() == user_id.strip():
            # Create a new dictionary that includes the Firebase key as 'project_id'
            # This makes it consistent with how you want to use it later
            project_data['project_id'] = project_id
            founder_projects_list.append(project_data)
    return founder_projects_list


def get_investments_for_projects(project_ids_list): # Renamed parameter for clarity
    investments_ref = db.reference('invested_projects')
    all_investments_records = investments_ref.get() or {} # Use a more descriptive name

    # Convert the dictionary of records to a list of records for easier filtering
    # all_investments_records is like: {'-OS-XcKYZJK-...': { ... investment data ... }}
    # We want to iterate over the values (the investment data dictionaries)
    investments_values = all_investments_records.values()

    found_investments = []
    for inv in investments_values:
        # Check if the 'project_id' in the investment record is in the provided list of project_ids
        if inv.get('project_id') in project_ids_list:
            found_investments.append(inv)
    return found_investments


def get_user_data(user_id):
    ref = db.reference(f'users/{user_id}')
    return ref.get()



# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvestmentPredictorError(Exception):
    """Custom exception for Investment Predictor errors"""
    pass


class InvestmentPredictor:
    """
    A class for making investment success predictions using pre-trained ML models.
    
    This class handles loading of saved models, preprocessing of input data,
    and generation of predictions with confidence intervals and risk assessments.
    """
    
    def __init__(self, models_dir: str = "saved_models"):
        """
        Initialize the Investment Predictor.
        
        Args:
            models_dir (str): Directory containing saved model files
        """
        self.models_dir = Path(models_dir)
        self.model = None
        self.scaler = None
        self.label_encoders = None
        self.feature_names = None
        self.categorical_columns = None
        self.model_info = None
        self.is_loaded = False
        
        # Expected feature columns (based on the notebook)
        self.expected_features = [
            'industry', 'target_market', 'business_model', 'traction',
            'funding_amount', 'time_to_funding', 'team_size', 'advisors_count',
            'partnerships_count', 'customer_acquisition_cost', 'lifetime_value',
            'monthly_recurring_revenue', 'churn_rate', 'market_size',
            'competition_level', 'technology_readiness', 'regulatory_compliance',
            'intellectual_property', 'geographic_reach', 'revenue_growth_rate',
            'burn_rate', 'runway_months'
        ]
        
        # Default values for missing features
        self.default_values = {
            'funding_amount': 500000,
            'time_to_funding': 12,
            'team_size': 5,
            'advisors_count': 2,
            'partnerships_count': 1,
            'customer_acquisition_cost': 100,
            'lifetime_value': 1000,
            'monthly_recurring_revenue': 10000,
            'churn_rate': 5.0,
            'market_size': 1000000000,
            'competition_level': 5,
            'technology_readiness': 7,
            'regulatory_compliance': 8,
            'intellectual_property': 5,
            'geographic_reach': 3,
            'revenue_growth_rate': 15.0,
            'burn_rate': 50000,
            'runway_months': 18
        }
        
        # Load models if directory exists
        if self.models_dir.exists():
            self.load_models()
    
    def load_models(self) -> bool:
        """
        Load all saved model components.
        
        Returns:
            bool: True if all models loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading models from {self.models_dir}")
            
            # Check if all required files exist
            required_files = [
                'feature_scaler.pkl',
                'label_encoders.pkl', 
                'feature_names.pkl',
                'categorical_columns.pkl',
                'model_metrics.pkl'
            ]
            
            missing_files = []
            for file in required_files:
                if not (self.models_dir / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                raise InvestmentPredictorError(
                    f"Missing required model files: {missing_files}\n"
                    f"Please run the Jupyter notebook first to train and save models."
                )
            
            # Load model info to find the best model file
            self.model_info = joblib.load(self.models_dir / 'model_metrics.pkl')
            best_model_name = self.model_info['best_model_name']
            model_filename = f"best_model_{best_model_name.lower().replace(' ', '_')}.pkl"
            
            if not (self.models_dir / model_filename).exists():
                raise InvestmentPredictorError(
                    f"Best model file not found: {model_filename}\n"
                    f"Expected model: {best_model_name}"
                )
            
            # Load all components
            self.model = joblib.load(self.models_dir / model_filename)
            self.scaler = joblib.load(self.models_dir / 'feature_scaler.pkl')
            self.label_encoders = joblib.load(self.models_dir / 'label_encoders.pkl')
            self.feature_names = joblib.load(self.models_dir / 'feature_names.pkl')
            self.categorical_columns = joblib.load(self.models_dir / 'categorical_columns.pkl')
            
            self.is_loaded = True
            logger.info(f"✅ Successfully loaded {best_model_name} model and all components")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading models: {str(e)}")
            self.is_loaded = False
            return False
    
    def _validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean input data.
        
        Args:
            data (Dict): Raw input data
            
        Returns:
            Dict: Validated and cleaned data
        """
        if not isinstance(data, dict):
            raise InvestmentPredictorError("Input data must be a dictionary")
        
        validated_data = {}
        
        # Check for required categorical features
        required_categorical = ['industry', 'target_market', 'business_model', 'traction']
        for col in required_categorical:
            if col not in data:
                raise InvestmentPredictorError(f"Missing required feature: {col}")
            validated_data[col] = str(data[col])
        
        # Add numerical features with defaults if missing
        for feature in self.expected_features:
            if feature in required_categorical:
                continue
                
            if feature in data:
                try:
                    validated_data[feature] = float(data[feature])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {feature}, using default")
                    validated_data[feature] = self.default_values.get(feature, 0)
            else:
                validated_data[feature] = self.default_values.get(feature, 0)
                logger.info(f"Using default value for missing feature: {feature}")
        
        return validated_data
    
    def _preprocess_data(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Preprocess input data for prediction.
        
        Args:
            data (Dict): Validated input data
            
        Returns:
            np.ndarray: Preprocessed feature array
        """
        if not self.is_loaded:
            raise InvestmentPredictorError("Models not loaded. Call load_models() first.")
        
        # Create DataFrame with single row
        df = pd.DataFrame([data])
        
        # Ensure all expected features are present
        for feature in self.expected_features:
            if feature not in df.columns:
                df[feature] = self.default_values.get(feature, 0)
        
        # Reorder columns to match training data
        df = df[self.expected_features]
        
        # Encode categorical variables
        for col in self.categorical_columns:
            if col in df.columns:
                if col in self.label_encoders:
                    try:
                        # Convert to string first
                        df[col] = df[col].astype(str)
                        
                        # Check if value exists in encoder classes
                        unique_values = df[col].unique()
                        for value in unique_values:
                            if value not in self.label_encoders[col].classes_:
                                # Use most frequent class as fallback
                                most_frequent = self.label_encoders[col].classes_[0]
                                logger.warning(
                                    f"Unknown category '{value}' for {col}, "
                                    f"using fallback: {most_frequent}"
                                )
                                df[col] = df[col].replace(value, most_frequent)
                        
                        # Transform the values
                        df[col] = self.label_encoders[col].transform(df[col])
                        
                    except Exception as e:
                        logger.error(f"Error encoding {col}: {str(e)}")
                        # Use mode value as fallback
                        df[col] = 0
        
        # Scale numerical features
        try:
            X_scaled = self.scaler.transform(df)
            return X_scaled
        except Exception as e:
            logger.error(f"Error scaling features: {str(e)}")
            raise InvestmentPredictorError(f"Preprocessing failed: {str(e)}")
    
    def predict_single(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction for a single investment opportunity.
        
        Args:
            data (Dict): Investment data with features
            
        Returns:
            Dict: Prediction results with confidence and risk assessment
        """
        if not self.is_loaded:
            raise InvestmentPredictorError(
                "Models not loaded. Please ensure the Jupyter notebook has been run "
                "and model files exist in the saved_models directory."
            )
        
        try:
            # Validate and preprocess data
            validated_data = self._validate_input(data)
            X_processed = self._preprocess_data(validated_data)
            
            # Make prediction
            prediction = self.model.predict(X_processed)[0]
            
            # Clip prediction to valid range [0, 1]
            prediction = np.clip(prediction, 0, 1)
            
            # Calculate confidence interval (if model supports it)
            confidence_interval = None
            try:
                if hasattr(self.model, 'predict_proba'):
                    # For classification models, get probability
                    proba = self.model.predict_proba(X_processed)[0]
                    confidence = max(proba)
                elif hasattr(self.model, 'score_samples'):
                    # For models with uncertainty estimation
                    confidence = self.model.score_samples(X_processed)[0]
                else:
                    # Simple confidence based on distance from extremes
                    confidence = 1 - abs(prediction - 0.5) * 2
            except:
                confidence = 0.7  # Default confidence
            
            # Risk assessment
            if prediction >= 0.7:
                risk_level = "Low"
                risk_emoji = "🟢"
                recommendation = "Recommended for investment"
            elif prediction >= 0.5:
                risk_level = "Medium"
                risk_emoji = "🟡"
                recommendation = "Consider with due diligence"
            else:
                risk_level = "High"
                risk_emoji = "🔴"
                recommendation = "High risk - proceed with caution"
            
            return {
                'success_probability': float(prediction),
                'confidence': float(confidence),
                'risk_level': risk_level,
                'risk_emoji': risk_emoji,
                'recommendation': recommendation,
                'model_name': self.model_info['best_model_name'],
                'prediction_percentile': f"{prediction * 100:.1f}%",
                'input_data': validated_data
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise InvestmentPredictorError(f"Prediction failed: {str(e)}")
    
    def predict_batch(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Make predictions for multiple investment opportunities.
        
        Args:
            data_list (List[Dict]): List of investment data dictionaries
            
        Returns:
            List[Dict]: List of prediction results
        """
        if not self.is_loaded:
            raise InvestmentPredictorError("Models not loaded.")
        
        results = []
        for i, data in enumerate(data_list):
            try:
                result = self.predict_single(data)
                result['index'] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Error predicting item {i}: {str(e)}")
                results.append({
                    'index': i,
                    'error': str(e),
                    'success_probability': None,
                    'risk_level': 'Error'
                })
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model and its performance.
        
        Returns:
            Dict: Model information and metrics
        """
        if not self.is_loaded:
            return {'error': 'Models not loaded'}
        
        return {
            'model_name': self.model_info['best_model_name'],
            'test_metrics': self.model_info['test_metrics'],
            'cv_scores': self.model_info['cv_scores'],
            'categorical_columns': self.categorical_columns,
            'feature_names': self.feature_names,
            'models_directory': str(self.models_dir),
            'is_loaded': self.is_loaded
        }
    
    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """
        Get feature importance from the model (if available).
        
        Args:
            top_n (int): Number of top features to return
            
        Returns:
            Dict: Feature importance scores
        """
        if not self.is_loaded:
            return {'error': 'Models not loaded'}
        
        try:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                feature_importance = dict(zip(self.feature_names, importances))
                # Sort by importance and return top_n
                sorted_features = sorted(feature_importance.items(), 
                                       key=lambda x: x[1], reverse=True)
                return dict(sorted_features[:top_n])
            elif hasattr(self.model, 'coef_'):
                # For linear models, use coefficient magnitudes
                coef = np.abs(self.model.coef_).flatten()
                feature_importance = dict(zip(self.feature_names, coef))
                sorted_features = sorted(feature_importance.items(), 
                                       key=lambda x: x[1], reverse=True)
                return dict(sorted_features[:top_n])
            else:
                return {'message': 'Feature importance not available for this model type'}
        except Exception as e:
            return {'error': f'Error getting feature importance: {str(e)}'}


# Django Integration Functions
def django_predict_investment(investment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Django-friendly function for single investment prediction.
    
    Args:
        investment_data (Dict): Investment data
        
    Returns:
        Dict: Prediction results
        
    Usage in Django views:
        from django_investment_predictor import django_predict_investment
        
        result = django_predict_investment({
            'industry': 'Technology',
            'target_market': 'B2B',
            'business_model': 'SaaS',
            'funding_amount': 1000000,
            # ... other features
        })
    """
    try:
        predictor = InvestmentPredictor()
        return predictor.predict_single(investment_data)
    except Exception as e:
        return {
            'error': str(e),
            'success_probability': None,
            'risk_level': 'Error'
        }


def django_predict_investments_batch(investments_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Django-friendly function for batch investment predictions.
    
    Args:
        investments_list (List[Dict]): List of investment data
        
    Returns:
        List[Dict]: List of prediction results
    """
    try:
        predictor = InvestmentPredictor()
        return predictor.predict_batch(investments_list)
    except Exception as e:
        return [{'error': str(e), 'success_probability': None, 'risk_level': 'Error'}]


def django_get_model_status() -> Dict[str, Any]:
    """
    Check if models are loaded and get basic info.
    
    Returns:
        Dict: Model status and basic information
    """
    try:
        predictor = InvestmentPredictor()
        return {
            'models_loaded': predictor.is_loaded,
            'model_info': predictor.get_model_info() if predictor.is_loaded else None
        }
    except Exception as e:
        return {
            'models_loaded': False,
            'error': str(e)
        }





# Example usage and testing
if __name__ == "__main__":
    """
    Example usage of the Investment Predictor.
    Run this script directly to test the functionality.
    """
    
    # Test data - example investment opportunity
    test_investment = {
        'industry': 'Technology',
        'target_market': 'B2B',
        'business_model': 'SaaS',
        'traction': 'Revenue',
        'funding_amount': 1000000,
        'time_to_funding': 6,
        'team_size': 8,
        'advisors_count': 3,
        'partnerships_count': 2,
        'customer_acquisition_cost': 150,
        'lifetime_value': 2000,
        'monthly_recurring_revenue': 50000,
        'churn_rate': 3.0,
        'market_size': 5000000000,
        'competition_level': 6,
        'technology_readiness': 8,
        'regulatory_compliance': 9,
        'intellectual_property': 7,
        'geographic_reach': 4,
        'revenue_growth_rate': 25.0,
        'burn_rate': 75000,
        'runway_months': 24
    }
    
    print("🚀 Investment Prediction System Test")
    print("=" * 50)
    
    try:
        # Test model loading
        predictor = InvestmentPredictor()
        
        if not predictor.is_loaded:
            print("❌ Models not loaded. Please run the Jupyter notebook first.")
            print("\n📋 Instructions:")
            print("1. Open and run investment_prediction_models.ipynb")
            print("2. Ensure all cells complete successfully")
            print("3. Verify saved_models directory is created")
            print("4. Run this script again")
            sys.exit(1)
        
        # Test single prediction
        print("🔍 Testing single prediction...")
        result = predictor.predict_single(test_investment)
        
        print(f"\n📊 Prediction Results:")
        print(f"Success Probability: {result['prediction_percentile']}")
        print(f"Risk Level: {result['risk_emoji']} {result['risk_level']}")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Model Used: {result['model_name']}")
        print(f"Confidence: {result['confidence']:.2f}")
        
        # Test batch prediction
        print("\n🔍 Testing batch prediction...")
        test_batch = [test_investment, test_investment.copy()]
        test_batch[1]['funding_amount'] = 500000
        test_batch[1]['industry'] = 'Healthcare'
        
        batch_results = predictor.predict_batch(test_batch)
        print(f"Batch prediction completed for {len(batch_results)} items")
        
        # Show model info
        print("\n📈 Model Information:")
        model_info = predictor.get_model_info()
        print(f"Best Model: {model_info['model_name']}")
        print(f"Test Metrics: {model_info['test_metrics']}")
        
        # Show feature importance
        print("\n🔝 Top Feature Importance:")
        importance = predictor.get_feature_importance(top_n=5)
        for feature, score in importance.items():
            print(f"  {feature}: {score:.4f}")
        
        print("\n✅ All tests completed successfully!")
        print("\n📖 Usage in Django:")
        print("from django_investment_predictor import django_predict_investment")
        print("result = django_predict_investment(investment_data)")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        sys.exit(1) 

        