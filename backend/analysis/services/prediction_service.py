# analysis/services/prediction_service.py
import numpy as np
from datetime import datetime, timedelta
from django.core.cache import cache
import yfinance as yf
from analysis.services.model_manager import ModelManager

class PredictionService:
    """
    High-level service for stock predictions
    Uses ModelManager for model lifecycle and StockPricePredictor for predictions
    """
    
    def __init__(self, symbol, cache_timeout=3600):
        self.symbol = symbol.upper()
        self.cache_timeout = cache_timeout
        self.manager = ModelManager()
        
        # Use ModelManager for model lifecycle
        self.model, self.scaler, self.metadata = self.manager.train_or_load_model(symbol)
        
        # Initialize predictor with the loaded model
        from analysis.ml_models.price_predictor import StockPricePredictor
        self.predictor = StockPricePredictor()
        self.predictor.model = self.model
        self.predictor.scaler = self.scaler
    
    def get_prediction_analysis(self, days=7):
        """
        Get comprehensive prediction analysis with caching
        """
        cache_key = f"prediction_{self.symbol}_{days}"
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Get predictions using the loaded model
            price_predictions = self.predictor.predict_future(self.symbol, days=days)
            
            # Get trading signal
            trading_signal = self.predictor.get_trading_signal(self.symbol)
            
            # Get current market data for context
            market_context = self._get_market_context()
            
            # Compile analysis
            analysis = {
                'symbol': self.symbol,
                'price_predictions': price_predictions,
                'trading_signal': trading_signal,
                'signal_confidence': self._calculate_signal_confidence(trading_signal, price_predictions),
                'market_context': market_context,
                'prediction_days': days,
                'timestamp': datetime.now().isoformat(),
                'model_used': True,
                'model_metadata': {
                    'version': self.metadata.get('version', 1),
                    'last_trained': self.metadata.get('last_trained'),
                    'training_metrics': self.metadata.get('training_metrics', {})
                },
                'disclaimer': 'FOR EDUCATIONAL PURPOSES ONLY - NOT FINANCIAL ADVICE'
            }
            
            # Cache the result
            cache.set(cache_key, analysis, self.cache_timeout)
            
            return analysis
            
        except Exception as e:
            print(f"Prediction service error for {self.symbol}: {str(e)}")
            return self._get_fallback_analysis()
    
    def get_quick_signal(self):
        """
        Get only trading signal (faster, uses signal-specific cache)
        """
        cache_key = f"signal_{self.symbol}"
        cached_signal = cache.get(cache_key)
        
        if cached_signal:
            return cached_signal
        
        try:
            # Use existing method from predictor
            signal = self.predictor.get_trading_signal(self.symbol)
            
            signal_data = {
                'symbol': self.symbol,
                'signal': signal,
                'timestamp': datetime.now().isoformat(),
                'model_version': self.metadata.get('version', 1)
            }
            
            # Cache signal for shorter time (15 minutes) since it changes faster
            cache.set(cache_key, signal_data, 900)  # 15 minutes
            
            return signal_data
            
        except Exception as e:
            print(f"Signal error for {self.symbol}: {str(e)}")
            return {
                'symbol': self.symbol,
                'signal': 'HOLD',
                'error': 'Signal generation failed',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_portfolio_predictions(self, symbols):
        """
        Get predictions for multiple symbols (optimized for portfolio view)
        """
        portfolio_predictions = {}
        
        for symbol in symbols:
            try:
                # For portfolio view, use a lightweight service instance per symbol
                if symbol != self.symbol:
                    symbol_service = PredictionService(symbol)
                    signal_data = symbol_service.get_quick_signal()
                else:
                    signal_data = self.get_quick_signal()
                    
                portfolio_predictions[symbol] = signal_data
            except Exception as e:
                portfolio_predictions[symbol] = {
                    'symbol': symbol,
                    'signal': 'HOLD',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return portfolio_predictions
    
    def _get_market_context(self):
        """
        Get current market data for the symbol
        """
        try:
            stock_data = yf.download(self.symbol, period='1mo', progress=False)
            if stock_data.empty:
                return {}
            
            current_price = stock_data['Close'].iloc[-1]
            prev_close = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
            day_change = current_price - prev_close
            day_change_percent = (day_change / prev_close) * 100
            
            # Calculate additional metrics
            high_52w = stock_data['Close'].tail(252).max() if len(stock_data) >= 252 else current_price
            low_52w = stock_data['Close'].tail(252).min() if len(stock_data) >= 252 else current_price
            
            return {
                'current_price': float(current_price),
                'day_change': float(day_change),
                'day_change_percent': float(day_change_percent),
                'volume': int(stock_data['Volume'].iloc[-1]) if 'Volume' in stock_data else None,
                'high_52_week': float(high_52w),
                'low_52_week': float(low_52w),
                'percent_from_high': float(((current_price - high_52w) / high_52w) * 100),
                'percent_from_low': float(((current_price - low_52w) / low_52w) * 100)
            }
        except Exception as e:
            print(f"Error getting market context for {self.symbol}: {str(e)}")
            return {}
    
    def _calculate_signal_confidence(self, signal, predictions):
        """
        Calculate confidence score based on signal strength and prediction consistency
        """
        if not predictions or len(predictions) < 2:
            return 0.5
        
        # Calculate prediction volatility (lower volatility = higher confidence)
        predictions_array = np.array(predictions)
        volatility = np.std(predictions_array) / np.mean(predictions_array)
        
        # Base confidence on signal strength
        signal_strength = {
            'STRONG_BUY': 0.9,
            'BUY': 0.7,
            'HOLD': 0.5,
            'SELL': 0.7,
            'STRONG_SELL': 0.9
        }
        
        base_confidence = signal_strength.get(signal, 0.5)
        
        # Adjust for prediction consistency
        if volatility < 0.02:  # Very consistent predictions
            confidence = min(base_confidence + 0.2, 0.95)
        elif volatility < 0.05:  # Moderately consistent
            confidence = base_confidence
        else:  # High volatility
            confidence = max(base_confidence - 0.2, 0.3)
        
        return round(confidence, 2)
    
    def _get_fallback_analysis(self):
        """
        Fallback analysis when prediction fails
        """
        market_context = self._get_market_context()
        
        return {
            'symbol': self.symbol,
            'price_predictions': None,
            'trading_signal': 'HOLD',
            'signal_confidence': 0.5,
            'market_context': market_context,
            'prediction_days': 7,
            'timestamp': datetime.now().isoformat(),
            'model_used': False,
            'error': 'Prediction service temporarily unavailable',
            'disclaimer': 'FOR EDUCATIONAL PURPOSES ONLY - NOT FINANCIAL ADVICE'
        }
    
    def clear_cache(self):
        """
        Clear all cached predictions for this symbol
        """
        cache_keys = [
            f"prediction_{self.symbol}_7",
            f"prediction_{self.symbol}_14", 
            f"prediction_{self.symbol}_30",
            f"signal_{self.symbol}"
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        return True
    
    def get_model_info(self):
        """Get detailed information about the current model"""
        return {
            'symbol': self.symbol,
            'metadata': self.metadata,
            'model_exists': self.manager.model_exists(self.symbol),
            'files': {
                'model': self.manager.get_model_path(self.symbol),
                'scaler': self.manager.get_scaler_path(self.symbol),
                'metadata': self.manager.get_metadata_path(self.symbol)
            },
            'cache_status': {
                'prediction_cache': bool(cache.get(f"prediction_{self.symbol}_7")),
                'signal_cache': bool(cache.get(f"signal_{self.symbol}"))
            }
        }
    
    def force_retrain(self):
        """Force retrain the model for this symbol"""
        try:
            self.model, self.scaler, self.metadata = self.manager.train_or_load_model(
                self.symbol, force_retrain=True
            )
            
            # Update predictor with new model
            self.predictor.model = self.model
            self.predictor.scaler = self.scaler
            
            # Clear cache since model has changed
            self.clear_cache()
            
            return True
        except Exception as e:
            print(f"Force retrain failed for {self.symbol}: {str(e)}")
            return False


# Factory function for easy usage
def get_prediction_service(symbol):
    """Factory function to get PredictionService instance"""
    return PredictionService(symbol)


# Utility function for batch operations
def get_batch_predictions(symbols):
    """Get predictions for multiple symbols efficiently"""
    predictions = {}
    
    for symbol in symbols:
        try:
            service = get_prediction_service(symbol)
            quick_signal = service.get_quick_signal()
            predictions[symbol] = quick_signal
        except Exception as e:
            predictions[symbol] = {
                'symbol': symbol,
                'signal': 'HOLD',
                'error': str(e)
            }
    
    return predictions