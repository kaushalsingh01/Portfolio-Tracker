#price_predictor.py
import numpy as np
import pandas as pd
from keras.models import Sequential, load_model
from keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf
from datetime import datetime, timedelta
import joblib
import os
from django.conf import settings


class StockPricePredictor:
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0,1))
        self.lookback_days = 60
        self.predication_cache = {}
        self.cache_timeout= 3600
        self.models_dir = os.path.join(settings.BASE_DIR, 'analysis', 'trained_models')
        
        # Create models directory if it doesn't exist
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Cache for loaded models to avoid repeated file I/O
        self.loaded_models = {}

    def prepare_data(self, symbol, period='2y'):
        try: 
            stock = yf.download(symbol, period=period, group_by='ticker')
            stock = stock.stack(level=0, future_stack=True).rename_axis(['Date', 'Ticker']).reset_index()
            if stock.empty:
                print(f"No data found for symbol: {symbol}")
                return None, None
            
            data = stock['Close'].values.reshape(-1, 1)

            if len(data) < self.lookback_days + 10:  # Need minimum data
                print(f"Insufficient data for {symbol}: {len(data)} points")
                return None, None
            
            scaled_data = self.scaler.fit_transform(data)
            x,y = [], []
            for i in range(self.lookback_days, len(scaled_data)):
                x.append(scaled_data[i-self.lookback_days:i, 0])
                y.append(scaled_data[i, 0])

            return np.array(x), np.array(y)
        except Exception as e:
            print(f"Error preparing data for {symbol}: {str(e)}")
            return None, None
        
    def build_model(self, input_shape):
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])

        model.compile(optimizer='adam', loss='mean_squared_error')
        return model
    
    def train_model(self, symbol):
        x, y = self.prepare_data(symbol=symbol)
        if x is None or y is None:
            return False
        
        x = x.reshape(x.shape[0], x.shape[1], 1)
        
        if len(x) < 10: 
            return False
        
        split = int(0.8 * len(x))
        x_train, x_val = x[:split], x[split:]
        y_train, y_val = y[:split], y[split:]

        self.model = self.build_model((x.shape[1],1))

        history = self.model.fit(
            x_train, y_train,
            batch_size=32,
            epochs=50,
            validation_data=(x_val, y_val),
            verbose=0
        )
        from analysis.services.model_manager import ModelManager
        manager = ModelManager()

        training_metrics = {
            'final_loss': float(history.history['loss'][-1]),
            'final_val_loss': float(history.history['val_loss'][-1]),
            'training_samples': len(x_train),
            'validation_samples': len(x_val)
        }

        success = manager.save_model(
            symbol=symbol,
            model=self.model,
            scaler=self.scaler,
            training_metrics=training_metrics
        )
        
        if success:
        # Cache the trained model
            self.loaded_models[symbol] = {
                'model': self.model,
                'scaler': self.scaler,
                'last_loaded': datetime.now()
            }
    
        return success
    
    def load_model(self, symbol):
        if symbol in self.loaded_models:
            return self.loaded_models[symbol]['model'], self.loaded_models[symbol]['scaler']
        
        model_path = os.path.join(self.models_dir, f'{symbol}_model.h5')
        scaler_path = os.path.join(self.models_dir, f'{symbol}_scaler.pkl')
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            return None, None
            
        try:
            model = load_model(model_path)
            scaler = joblib.load(scaler_path)
            
            self.loaded_models[symbol] = {
                'model': model,
                'scaler': scaler,
                'last_loaded': datetime.now()
            }
            
            return model, scaler
        except Exception as e:
            print(f"Error loading model for {symbol}: {str(e)}")
            return None, None
    
    def model_exists(self, symbol):
        model_path = os.path.join(self.models_dir, f'{symbol}_model.h5')
        scaler_path = os.path.join(self.models_dir, f'{symbol}_scaler.pkl')
        return os.path.exists(model_path) and os.path.exists(scaler_path)

    def predict_future(self, symbol, days=7):
        cache_key = (symbol, days)

        if cache_key in self.perdication_cache:
            cached = self.perdication_cache[cache_key]
            if(datetime.now() - cached["timestamp"]).total_seconds() < self.cache_timeout:
                return cached["predictions"]
            
        model, scaler = self.load_model(symbol)
        if model is None or scaler is None:
            print(f"No trained model found for {symbol}")
            return None

        try:

            model_path = os.path.join(self.models_dir, f'{symbol}_model.h5')
            scaler_path = os.path.join(self.models_dir, f'{symbol}_scaler.pkl')

            self.model.save(model_path)
            joblib.dump(self.scaler, scaler_path)

            stock_data = yf.download(symbol, period='3mo', group_by='ticker')
            stock_data = stock_data.stack(level=0, future_stack=True).rename_axis(['Date', 'Ticker']).reset_index()
            if stock_data.empty:
                return None
                
            recent_prices = stock_data['Close'].values[-self.lookback_days:]

            if len(recent_prices) < self.lookback_days:
                print(f"Insufficient recent data for {symbol}")
                return None
            
            scaled_data = self.scaler.transform(recent_prices.reshape(-1, 1))
            x_pred = scaled_data.reshape(1, self.lookback_days, 1)

            predictions = []
            current_sequence = x_pred.copy()

            for _ in range(days):
                next_pred = self.model.predict(current_sequence, verbose=0)
                predictions.append(next_pred[0,0])

                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0,-1, 0] = next_pred[0, 0]

            predictions = np.array(predictions). reshape(-1, 1)
            predictions = self.scaler.inverse_transform(predictions)
            predictions_list = predictions.flatten().tolist()

            self.predication_cache[cache_key]  = {
                "timestamp": datetime.now(),
                "predictions": predictions_list
            }

            return predictions_list
        
        except Exception as e:
            print(f"Prediction error for {symbol}: {str(e)}")
            return None
    
    def get_trading_signal(self, symbol):
        if not self.model_exists(symbol):
            print(f"Training model for {symbol}...")
            if not self.train_model(symbol):
                return "HOLD"

        predictions = self.predict_future(symbol=symbol, days=5)
        if not predictions:
            return "HOLD"
        
        try:
            # Get current price
            current_data = yf.download(symbol, period='1d', progress=False)
            if current_data.empty:
                return "HOLD"
                
            current_price = current_data['Close'].iloc[-1]
            avg_prediction = np.mean(predictions)
            change_percentage = (avg_prediction - current_price) / current_price * 100

            if change_percentage > 2:
                return "STRONG_BUY"
            elif change_percentage > 0.5:
                return "BUY"
            elif change_percentage < -2:
                return "STRONG_SELL"
            elif change_percentage < -0.5:
                return "SELL"
            else:
                return "HOLD"
                
        except Exception as e:
            print(f"Error generating signal for {symbol}: {str(e)}")
            return "HOLD"
