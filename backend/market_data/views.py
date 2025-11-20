from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Stock
from .serializers import StockSerializer, StockDetailSerializer, StockSearchSerializer, HistoricalDataSerializer
from .services.stock_service import StockService

class StockViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Stock.object.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return StockSearchSerializer
        elif self.action == 'retrieve':
            return StockDetailSerializer
        return StockSerializer
    
    def get_queryset(self):
        queryset = super().get_querysets()
        search_query = self.request.query_params.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(symbol__icontains=search_query) | 
                Q(company_name__icontains=search_query)
            )
        return queryset
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        stock = self.get_object()
        period = request.query_params.get('period', '1mo')
        interval = request.query_params.get('interval', '1d')

        try:
            historical_data = StockService.get_historical_data(
                stock.symbol,
                period=period,
                interval=interval
            )

            serializer = HistoricalDataSerializer(historical_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error":f"Failed to fetch historical data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=True, methods=['get'])
    def quote(self, request, pk=None):
        stock = self.get_object()
        try:
            quote_data = StockService.get_real_time_quote(stock.symbol)
            return Response(quote_data)
        
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch quote: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        popular_symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA']
        popular_stocks = Stock.objects.filter(symbol__in=popular_symbols)
        serailzer = StockSearchSerializer(popular_stocks, many=True)
        return Response(serailzer.data)
    
class StockSearchViewset(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))
        if not query or len(query) < 2:
            return Response(
                {"error":"Search query must be at lest 2 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        stocks = Stock.objects.filter(
            Q(symbol__icontains=query) | 
            Q(company_name__icontains=query)
        )[:limit]

        if not stocks.exists():
            try:
                external_results = StockService.search_stocks(query)
                return Response(external_results)
            except Exception as e:
                return Response(
                    {"error": f"Search failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)