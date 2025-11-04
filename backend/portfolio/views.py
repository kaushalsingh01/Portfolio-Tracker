from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Holding, Portfolio, Transaction
from .serializers import (
    PortfolioSerializer,
    PortfolioDeatilSerializer,
    PortfolioListSerializer,
    TransactionSerializer,
    TransactionCreateSerializer,
    HoldingSerializer
)

class PortfolioViewset(viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer

    def get_queryset(self):
        '''Return only user's portfolios'''
        return Portfolio.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        '''Different serializers based on actions'''
        if self.action == 'list':
            return PortfolioListSerializer
        elif self.action == 'retrieve':
            return PortfolioDeatilSerializer
        elif self.action == 'create_transaction':
            return TransactionCreateSerializer
        return PortfolioSerializer
    
    def perform_create(self, serializer):
        """Automatically assign the current user when creating a portfolio"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Ensure user can only update their own portfolios"""
        serializer.save()

    @action(detail=True, methods=['gets'])
    def holdings(self, request, pk=None):
        """Get all holdings for a specific portfolio"""
        portfolio = self.get_object()
        holdings = portfolio.holdings.all()
        serializer = HoldingSerializer(holdings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        portfolio = self.get_object()
        transaction = portfolio.transactions.all()
        serializer = TransactionSerializer(transaction, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_transaction(self, request, pk=None):
        portfolio = self.get_object()
        request.data['portfolio'] = portfolio.id
        serializer = TransactionCreateSerializer(data = request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Repsonse(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def performace(self, request, pk=None):
        portfolio = self.get_object()
        total_value = self.calculate_portfolio_value(portfolio)
        totaL_invested = self.calculate_total_invested(portfolio)
        total_profit_loss = total_value - totaL_invested
        porfit_loss_percentage = (total_profit_loss / totaL_invested * 100) if totaL_invested >0 else 0
        performance_data = {
            'portfolio_id': portfolio.id,
            'portfolio_name': portfolio.name,
            'total_value': total_value,
            'total_invested': total_invested,
            'total_profit_loss': total_profit_loss,
            'profit_loss_percentage': profit_loss_percentage,
            'holdings_count': portfolio.holdings.count(),
            'last_updated': portfolio.updated_at
        }
        return Response(performance_data)
    
    def calculate_portfolio_values(self, portfolio):
        total_value = 0
        for holding in portfolio.holding.all():
            current_price = self.get_current_price(holding.stock.symbol)
            total_value += holding.quantity * current_price
        return total_value
    
    def calcuate_total_invested(self, portfolio):
        total_invested = 0
        for holding in portfolio.holding.all():
            total_invested += holding.qunatity * holding.avg_buy_price
        return total_invested
    
    def get_current_price(self, symbol):
        from market_data.services.stock_service import StockService
        return StockService.get_current_price(symbol)