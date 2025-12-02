# analysis/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from datetime import datetime
from portfolio.models import Portfolio
from market_data.models import Stock
from analysis.services.prediction_service import PredictionService, get_prediction_service
from analysis.services.model_manager import ModelManager
from analysis.sentiment.news_analyzer import NewsSentimentAnalyzer
from analysis.services.portfolio_analyzer import PortfolioAnalyzer

# ============================================================================
# Portfolio Analysis ViewSet
# ============================================================================

class PortfolioAnalysisViewSet(viewsets.ViewSet):
    """Portfolio analysis and insights endpoints"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user).prefetch_related("holdings__stock")

    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        """Get comprehensive portfolio analysis"""
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        try:
            analysis = PortfolioAnalyzer.analyze_portfolio(portfolio)
            return Response(analysis)
        except Exception as e:
            return Response(
                {'error': f'Analysis failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get portfolio performance breakdown"""
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        try:
            performance_data = PortfolioAnalyzer.get_performance_analysis(portfolio)
            return Response(performance_data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def sectors(self, request, pk=None):
        """Get sector allocation analysis"""
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        try:
            sector_data = PortfolioAnalyzer.get_sector_analysis(portfolio)
            return Response(sector_data)
        except Exception as e:
            return Response(
                {'error': f'Sector analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def risk(self, request, pk=None):
        """Get portfolio risk assessment"""
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        try:
            risk_data = PortfolioAnalyzer.get_holding_analysis(portfolio)
            return Response(risk_data)
        except Exception as e:
            return Response(
                {'error': f'Risk analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def compare_portfolios(self, request):
        """Compare all user portfolios"""
        portfolios = self.get_queryset()
        
        comparison_data = []
        for portfolio in portfolios:
            try:
                basic_metrics = PortfolioAnalyzer.get_basic_metrics(portfolio)
                comparison_data.append({
                    'id': portfolio.id,
                    'name': portfolio.name,
                    'description': portfolio.description,
                    'created_at': portfolio.created_at,
                    **basic_metrics
                })
            except Exception as e:
                # Skip portfolios that fail analysis
                continue
        
        return Response(comparison_data)

    @action(detail=True, methods=['get'])
    def holdings_analysis(self, request, pk=None):
        """Get detailed analysis for each holding in portfolio"""
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        
        holdings_data = []
        for holding in portfolio.holdings.all():
            try:
                current_value = holding.get_current_value()
                profit_loss = holding.get_profit_loss()
                profit_loss_percentage = holding.get_profit_loss_percentage()
                
                holdings_data.append({
                    'symbol': holding.stock.symbol,
                    'company_name': holding.stock.company_name,
                    'sector': holding.stock.sector,
                    'quantity': holding.quantity,
                    'avg_buy_price': holding.avg_buy_price,
                    'current_value': float(current_value),
                    'profit_loss': float(profit_loss),
                    'profit_loss_percentage': float(profit_loss_percentage),
                    'weight_in_portfolio': float(current_value / portfolio.get_current_value() * 100) if portfolio.get_current_value() > 0 else 0
                })
            except Exception as e:
                # Skip holdings that fail analysis
                continue
        
        return Response({
            'portfolio_id': pk,
            'portfolio_name': portfolio.name,
            'holdings_analysis': holdings_data
        })

# ============================================================================
# Portfolio Prediction ViewSet
# ============================================================================

class PortfolioPredictionViewSet(viewsets.ViewSet):
    """Stock prediction endpoints for portfolio-related predictions"""
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def portfolio_predictions(self, request, pk=None):
        """Get AI predictions for all stocks in a portfolio"""
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        
        try:
            symbols = [holding.stock.symbol for holding in portfolio.holdings.all()]
            
            if not symbols:
                return Response({
                    'portfolio_id': pk,
                    'portfolio_name': portfolio.name,
                    'predictions': {},
                    'message': 'No stocks in portfolio'
                })
            
            # Use first symbol to initialize service, then get batch predictions
            service = get_prediction_service(symbols[0])
            portfolio_predictions = service.get_portfolio_predictions(symbols)
            
            # Generate summary
            signal_counts = {}
            for prediction in portfolio_predictions.values():
                signal = prediction.get('signal', 'HOLD')
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            return Response({
                'portfolio_id': pk,
                'portfolio_name': portfolio.name,
                'predictions': portfolio_predictions,
                'summary': {
                    'total_stocks': len(symbols),
                    'signal_distribution': signal_counts,
                    'overall_sentiment': self._calculate_overall_sentiment(signal_counts)
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Portfolio prediction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_overall_sentiment(self, signal_counts):
        """Calculate overall portfolio sentiment from signals"""
        bullish = signal_counts.get('STRONG_BUY', 0) + signal_counts.get('BUY', 0)
        bearish = signal_counts.get('STRONG_SELL', 0) + signal_counts.get('SELL', 0)
        total = sum(signal_counts.values())
        
        if total == 0:
            return 'NEUTRAL'
        
        bullish_ratio = bullish / total
        bearish_ratio = bearish / total
        
        if bullish_ratio > 0.6:
            return 'STRONGLY_BULLISH'
        elif bullish_ratio > 0.4:
            return 'BULLISH'
        elif bearish_ratio > 0.6:
            return 'STRONGLY_BEARISH'
        elif bearish_ratio > 0.4:
            return 'BEARISH'
        else:
            return 'NEUTRAL'


# ============================================================================
# Stock Prediction ViewSet
# ============================================================================

class StockPredictionViewSet(viewsets.ViewSet):
    """ViewSet for stock predictions and signals"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='symbol/(?P<symbol>[^/.]+)')
    def stock_prediction(self, request, symbol=None):
        """Get comprehensive prediction analysis for a single stock"""
        try:
            # Validate symbol exists in database
            stock = get_object_or_404(Stock, symbol=symbol.upper())
            
            service = get_prediction_service(symbol)
            analysis = service.get_prediction_analysis(days=7)
            
            return Response(analysis)
            
        except Exception as e:
            return Response(
                {'error': f'Prediction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='signal/(?P<symbol>[^/.]+)')
    def quick_signal(self, request, symbol=None):
        """Get quick trading signal only"""
        try:
            service = get_prediction_service(symbol)
            signal_data = service.get_quick_signal()
            
            return Response(signal_data)
            
        except Exception as e:
            return Response(
                {
                    'symbol': symbol,
                    'signal': 'HOLD',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='cache/clear/(?P<symbol>[^/.]+)')
    def clear_prediction_cache(self, request, symbol=None):
        """Clear cached predictions for a symbol"""
        try:
            service = get_prediction_service(symbol)
            service.clear_cache()
            
            return Response({'status': f'Cache cleared for {symbol}'})
            
        except Exception as e:
            return Response(
                {'error': f'Cache clearance failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='batch-signals')
    def batch_signals(self, request):
        """Get signals for multiple symbols"""
        symbols = request.query_params.get('symbols', '')
        if not symbols:
            return Response(
                {'error': 'Symbols parameter required (comma-separated)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        try:
            # Use the first symbol to initialize service, then get batch predictions
            if symbol_list:
                service = get_prediction_service(symbol_list[0])
                predictions = service.get_portfolio_predictions(symbol_list)
                return Response(predictions)
            else:
                return Response({})
                
        except Exception as e:
            return Response(
                {'error': f'Batch prediction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# Sentiment Analysis ViewSet
# ============================================================================

class SentimentAnalysisViewSet(viewsets.ViewSet):
    """ViewSet for stock sentiment analysis"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='stock/(?P<symbol>[^/.]+)')
    def stock_sentiment(self, request, symbol=None):
        """Get sentiment analysis for a stock"""
        try:
            stock = get_object_or_404(Stock, symbol=symbol.upper())
            analyzer = NewsSentimentAnalyzer()
            sentiment = analyzer.get_stock_sentiment(symbol, stock.company_name)
            
            return Response(sentiment)
            
        except Exception as e:
            return Response(
                {'error': f'Sentiment analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='portfolio/(?P<portfolio_id>[^/.]+)')
    def portfolio_sentiment(self, request, portfolio_id=None):
        """Get sentiment analysis for all stocks in a portfolio"""
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
        
        symbols = [holding.stock.symbol for holding in portfolio.holdings.all()]
        analyzer = NewsSentimentAnalyzer()
        
        sentiment_results = {}
        for symbol in symbols:
            try:
                stock = Stock.objects.get(symbol=symbol)
                sentiment = analyzer.get_stock_sentiment(symbol, stock.company_name)
                sentiment_results[symbol] = sentiment
            except Exception as e:
                sentiment_results[symbol] = {
                    'symbol': symbol,
                    'error': str(e)
                }
        
        # Calculate overall portfolio sentiment
        sentiment_scores = [s.get('sentiment_score', 0) for s in sentiment_results.values() 
                          if isinstance(s, dict) and 'sentiment_score' in s]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        return Response({
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'sentiments': sentiment_results,
            'overall_sentiment_score': avg_sentiment,
            'overall_sentiment': 'BULLISH' if avg_sentiment > 0.1 else 'BEARISH' if avg_sentiment < -0.1 else 'NEUTRAL'
        })


# ============================================================================
# Model Management ViewSet
# ============================================================================

class ModelManagementViewSet(viewsets.ViewSet):
    """ViewSet for AI model management"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def model_management(self, request):
        """Get overall model management information"""
        manager = ModelManager()
        stats = manager.get_model_stats()
        models = manager.list_models()
        
        return Response({
            'model_statistics': stats,
            'trained_models': models
        })

    @action(detail=False, methods=['get'], url_path='model-status/(?P<symbol>[^/.]+)')
    def model_status(self, request, symbol=None):
        """Get status of a specific model"""
        manager = ModelManager()
        
        try:
            model_exists = manager.model_exists(symbol)
            metadata = manager.load_metadata(symbol) if model_exists else {}
            
            return Response({
                'symbol': symbol,
                'model_exists': model_exists,
                'metadata': metadata,
                'files': {
                    'model': manager.get_model_path(symbol),
                    'scaler': manager.get_scaler_path(symbol),
                    'metadata': manager.get_metadata_path(symbol)
                }
            })
        except Exception as e:
            return Response(
                {'error': f'Model status check failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='retrain/(?P<symbol>[^/.]+)')
    def retrain_model(self, request, symbol=None):
        """Force retrain a specific model"""
        manager = ModelManager()
        try:
            model, scaler, metadata = manager.train_or_load_model(symbol, force_retrain=True)
            return Response({
                'status': f'Model retrained successfully for {symbol}',
                'version': metadata.get('version'),
                'last_trained': metadata.get('last_trained')
            })
        except Exception as e:
            return Response(
                {'error': f'Retraining failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['delete'], url_path='delete/(?P<symbol>[^/.]+)')
    def delete_model(self, request, symbol=None):
        """Delete model files for a symbol"""
        manager = ModelManager()
        success = manager.delete_model(symbol)
        
        if success:
            return Response({'status': f'Model deleted for {symbol}'})
        else:
            return Response(
                {'error': f'Failed to delete model for {symbol}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def list_models(self, request):
        """List all available trained models"""
        manager = ModelManager()
        models = manager.list_models()
        
        return Response({
            'total_models': len(models),
            'models': models
        })

    @action(detail=False, methods=['get'])
    def old_models(self, request):
        """Get models that need retraining"""
        days = int(request.query_params.get('days', 30))
        manager = ModelManager()
        old_models = manager.get_old_models(days=days)
        
        return Response({
            'days_threshold': days,
            'old_models': old_models,
            'count': len(old_models)
        })


# ============================================================================
# System Health ViewSet
# ============================================================================

class SystemHealthViewSet(viewsets.ViewSet):
    """ViewSet for system health checks"""
    permission_classes = [AllowAny]  # Allow any for health checks

    @action(detail=False, methods=['get'])
    def analysis_health(self, request):
        """Health check for analysis services"""
        try:
            manager = ModelManager()
            stats = manager.get_model_stats()
            
            # Test prediction service with a common symbol
            service = get_prediction_service('AAPL')
            test_prediction = service.get_quick_signal()
            
            # Test sentiment analyzer
            sentiment_analyzer = NewsSentimentAnalyzer()
            test_sentiment = sentiment_analyzer.get_stock_sentiment('AAPL', 'Apple Inc.')
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'trained_models': stats['total_models'],
                'services': {
                    'model_manager': 'operational',
                    'prediction_service': 'operational',
                    'sentiment_analyzer': 'operational',
                    'portfolio_analyzer': 'operational'
                },
                'tests': {
                    'prediction_service': 'pass' if test_prediction.get('signal') else 'fail',
                    'sentiment_analyzer': 'pass' if test_sentiment.get('overall_sentiment') else 'fail',
                    'model_manager': 'pass' if stats['total_models'] >= 0 else 'fail'
                }
            }
            
            return Response(health_status)
            
        except Exception as e:
            return Response(
                {
                    'status': 'degraded',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'services': {
                        'model_manager': 'degraded',
                        'prediction_service': 'degraded', 
                        'sentiment_analyzer': 'degraded',
                        'portfolio_analyzer': 'degraded'
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['get'])
    def service_status(self, request):
        """Get detailed status of all services"""
        try:
            manager = ModelManager()
            stats = manager.get_model_stats()
            
            # Check each service individually
            services_status = {}
            
            # Model Manager Status
            try:
                models = manager.list_models()
                services_status['model_manager'] = {
                    'status': 'operational',
                    'details': f'{len(models)} models available',
                    'models_count': len(models)
                }
            except Exception as e:
                services_status['model_manager'] = {
                    'status': 'degraded',
                    'error': str(e)
                }
            
            # Prediction Service Status
            try:
                service = get_prediction_service('AAPL')
                signal = service.get_quick_signal()
                services_status['prediction_service'] = {
                    'status': 'operational',
                    'details': f"Test signal: {signal.get('signal')}",
                    'test_symbol': 'AAPL'
                }
            except Exception as e:
                services_status['prediction_service'] = {
                    'status': 'degraded', 
                    'error': str(e)
                }
            
            # Sentiment Analyzer Status
            try:
                analyzer = NewsSentimentAnalyzer()
                sentiment = analyzer.get_stock_sentiment('AAPL', 'Apple Inc.')
                services_status['sentiment_analyzer'] = {
                    'status': 'operational',
                    'details': f"Test sentiment: {sentiment.get('overall_sentiment')}",
                    'test_symbol': 'AAPL'
                }
            except Exception as e:
                services_status['sentiment_analyzer'] = {
                    'status': 'degraded',
                    'error': str(e)
                }
            
            return Response({
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy' if all(
                    s['status'] == 'operational' for s in services_status.values()
                ) else 'degraded',
                'services': services_status
            })
            
        except Exception as e:
            return Response(
                {
                    'timestamp': datetime.now().isoformat(),
                    'overall_status': 'unavailable',
                    'error': str(e)
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


# ============================================================================
# Combined Analysis ViewSet (All-in-one endpoint)
# ============================================================================

class CombinedAnalysisViewSet(viewsets.ViewSet):
    """ViewSet for combined stock analysis (prediction + sentiment)"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='stock/(?P<symbol>[^/.]+)')
    def combined_analysis(self, request, symbol=None):
        """Get combined prediction and sentiment analysis for a stock"""
        try:
            stock = get_object_or_404(Stock, symbol=symbol.upper())
            
            # Get prediction analysis
            prediction_service = get_prediction_service(symbol)
            prediction_analysis = prediction_service.get_prediction_analysis(days=7)
            
            # Get sentiment analysis
            sentiment_analyzer = NewsSentimentAnalyzer()
            sentiment_analysis = sentiment_analyzer.get_stock_sentiment(symbol, stock.company_name)
            
            # Combine analyses
            combined_analysis = {
                'symbol': symbol,
                'company_name': stock.company_name,
                'sector': stock.sector,
                'prediction': prediction_analysis,
                'sentiment': sentiment_analysis,
                'combined_recommendation': self._calculate_combined_recommendation(
                    prediction_analysis, 
                    sentiment_analysis
                ),
                'timestamp': datetime.now().isoformat(),
                'disclaimer': 'FOR EDUCATIONAL PURPOSES ONLY - NOT FINANCIAL ADVICE'
            }
            
            return Response(combined_analysis)
            
        except Exception as e:
            return Response(
                {'error': f'Combined analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_combined_recommendation(self, prediction, sentiment):
        """Calculate combined recommendation from prediction and sentiment"""
        # Map signals to numeric scores
        prediction_map = {
            'STRONG_BUY': 2,
            'BUY': 1,
            'HOLD': 0,
            'SELL': -1,
            'STRONG_SELL': -2
        }
        
        sentiment_map = {
            'BULLISH': 1,
            'NEUTRAL': 0,
            'BEARISH': -1
        }
        
        pred_score = prediction_map.get(prediction.get('trading_signal', 'HOLD'), 0)
        sentiment_score = sentiment_map.get(sentiment.get('overall_sentiment', 'NEUTRAL'), 0)
        
        # Weighted combination (70% prediction, 30% sentiment)
        combined_score = (pred_score * 0.7) + (sentiment_score * 0.3)
        
        if combined_score >= 1.5:
            return 'STRONG_BUY'
        elif combined_score >= 0.5:
            return 'BUY'
        elif combined_score <= -1.5:
            return 'STRONG_SELL'
        elif combined_score <= -0.5:
            return 'SELL'
        else:
            return 'HOLD'