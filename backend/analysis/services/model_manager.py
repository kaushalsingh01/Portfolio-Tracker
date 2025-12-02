# analysis/services/model_manager.py
import os
import joblib
import pandas as pd
from datetime import datetime
from django.conf import settings
from keras.models import load_model
import json

class ModelManager:  
    def __init__(self):
        self.models_dir = os.path.join(settings.BASE_DIR, "analysis", "trained_models")
        self.metadata_dir = os.path.join(settings.BASE_DIR, "analysis", "model_metadata")
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def get_model_path(self, symbol):
        return os.path.join(self.models_dir, f"{symbol}_model.h5")
    
    def get_scaler_path(self, symbol):
        return os.path.join(self.models_dir, f"{symbol}_scaler.pkl")
    
    def get_metadata_path(self, symbol):
        return os.path.join(self.metadata_dir, f"{symbol}_metadata.json")
   
    def model_exists(self, symbol):
        return (os.path.exists(self.get_model_path(symbol)) and 
                os.path.exists(self.get_scaler_path(symbol)))
    
    def metadata_exists(self, symbol):
        return os.path.exists(self.get_metadata_path(symbol))
    
    def load_model(self, symbol):
        if not self.model_exists(symbol):
            raise FileNotFoundError(f"No trained model found for {symbol}")
        
        try:
            model = load_model(self.get_model_path(symbol))
            scaler = joblib.load(self.get_scaler_path(symbol))
            return model, scaler
        except Exception as e:
            raise Exception(f"Error loading model for {symbol}: {str(e)}")
    
    def load_metadata(self, symbol):
        if not self.metadata_exists(symbol):
            return self._create_default_metadata(symbol)
        
        try:
            with open(self.get_metadata_path(symbol), 'r') as f:
                return json.load(f)
        except:
            return self._create_default_metadata(symbol)
    
    def save_model(self, symbol, model, scaler, training_metrics=None):
        try:
            model.save(self.get_model_path(symbol))
            joblib.dump(scaler, self.get_scaler_path(symbol))
            
            metadata = self.load_metadata(symbol)
            metadata.update({
                'last_trained': datetime.now().isoformat(),
                'training_metrics': training_metrics or {},
                'symbol': symbol,
                'version': metadata.get('version', 0) + 1
            })
            
            with open(self.get_metadata_path(symbol), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Model saved for {symbol} (version {metadata['version']})")
            return True
            
        except Exception as e:
            print(f"Error saving model for {symbol}: {str(e)}")
            return False
    
    def train_or_load_model(self, symbol, force_retrain=False):
        from analysis.ml_models.price_predictor import StockPricePredictor
        
        if not force_retrain and self.model_exists(symbol):
            try:
                model, scaler = self.load_model(symbol)
                metadata = self.load_metadata(symbol)
                print(f"Loaded existing model for {symbol}")
                return model, scaler, metadata
            except Exception as e:
                print(f"Error loading existing model for {symbol}: {str(e)}")
        
        print(f"Training new model for {symbol}...")
        predictor = StockPricePredictor()
        success = predictor.train_model(symbol)
        
        if success:
            model, scaler = self.load_model(symbol)
            metadata = self.load_metadata(symbol)
            
            metadata.update({
                'training_status': 'success',
                'last_trained': datetime.now().isoformat()
            })
            self._save_metadata(symbol, metadata)
            
            return model, scaler, metadata
        else:
            raise Exception(f"Model training failed for {symbol}")

    def list_models(self):
        models = []
        for filename in os.listdir(self.models_dir):
            if filename.endswith("_model.h5"):
                symbol = filename.replace("_model.h5", "")
                metadata = self.load_metadata(symbol)
                models.append({
                    'symbol': symbol,
                    'model_path': self.get_model_path(symbol),
                    'metadata': metadata
                })
        return models
    
    def get_old_models(self, days=30):
        old_models = []
        for model_info in self.list_models():
            metadata = model_info['metadata']
            last_trained = metadata.get('last_trained')
            
            if last_trained:
                last_trained_dt = datetime.fromisoformat(last_trained.replace('Z', '+00:00'))
                days_old = (datetime.now().replace(tzinfo=last_trained_dt.tzinfo) - last_trained_dt).days
                
                if days_old > days:
                    old_models.append({
                        'symbol': model_info['symbol'],
                        'days_old': days_old,
                        'last_trained': last_trained
                    })
        
        return old_models
    
    def delete_model(self, symbol):
        try:
            files_to_delete = [
                self.get_model_path(symbol),
                self.get_scaler_path(symbol), 
                self.get_metadata_path(symbol)
            ]
            
            deleted_count = 0
            for file_path in files_to_delete:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
            
            print(f"Deleted {deleted_count} files for {symbol}")
            return deleted_count > 0
            
        except Exception as e:
            print(f"Error deleting model for {symbol}: {str(e)}")
            return False
    
    def get_model_stats(self):
        models = self.list_models()
        old_models = self.get_old_models(days=30)
        
        return {
            'total_models': len(models),
            'models_need_retraining': len(old_models),
            'oldest_model': min(
                [m['metadata'].get('last_trained', '') for m in models], 
                key=lambda x: x if x else '9999'
            ) if models else None,
            'recently_trained': len([m for m in models 
                                   if self._is_recently_trained(m['metadata'])]),
            'model_symbols': [m['symbol'] for m in models]
        }
    
    def _create_default_metadata(self, symbol):
        return {
            'symbol': symbol,
            'version': 1,
            'created': datetime.now().isoformat(),
            'last_trained': datetime.now().isoformat(),
            'training_status': 'unknown',
            'training_metrics': {}
        }
    
    def _save_metadata(self, symbol, metadata):
        try:
            with open(self.get_metadata_path(symbol), 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving metadata for {symbol}: {str(e)}")
            return False
    
    def _is_recently_trained(self, metadata, days=7):
        last_trained = metadata.get('last_trained')
        if not last_trained:
            return False
        
        try:
            last_trained_dt = datetime.fromisoformat(last_trained.replace('Z', '+00:00'))
            days_old = (datetime.now().replace(tzinfo=last_trained_dt.tzinfo) - last_trained_dt).days
            return days_old <= days
        except:
            return False