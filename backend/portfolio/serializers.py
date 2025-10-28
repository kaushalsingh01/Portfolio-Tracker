from rest_framework import serializers
from django.db import models
from .models import Portfolio, Holding, Transaction
from market_data.serializers import StockSerializer

class PortfolioSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    holdings_count = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ('id', 'user', 'name', 'description', 'created_at',
                  'updated_at', 'holdings_count', 'total_value')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def get_holdings_count(self, obj):
        return obj.holdings.count()

    def get_total_value(self, obj):
        # Placeholder for actual logic
        return None

    def validate_name(self, value):
        user = self.context['request'].user
        existing = Portfolio.objects.filter(user=user, name=value)
        if self.instance:
            if self.instance.name != value and existing.exists():
                raise serializers.ValidationError("You already have a portfolio with this name.")
        elif existing.exists():
            raise serializers.ValidationError("You already have a portfolio with this name.")
        return value
    
class HoldingSerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.company_name', read_only=True)
    current_price = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()
    total_invested = serializers.SerializerMethodField()
    profit_loss = serializers.SerializerMethodField()
    profit_loss_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Holding
        fields = ('id', 'portfolio', 'stock', 'stock_symbol', 'stock_name',
                  'quantity', 'avg_buy_price', 'current_price', 'current_value',
                  'total_invested', 'profit_loss', 'profit_loss_percentage')
        read_only_fields = ('id', 'portfolio', 'stock_symbol', 'stock_name',
                            'current_price', 'current_value', 'total_invested',
                            'profit_loss', 'profit_loss_percentage')

    def get_current_price(self, obj):
        from market_data.services.stock_service import StockService
        return StockService.get_current_price(obj.stock.symbol)

    def get_current_value(self, obj):
        return obj.quantity * self.get_current_price(obj)

    def get_total_invested(self, obj):
        return obj.quantity * obj.avg_buy_price

    def get_profit_loss(self, obj):
        return self.get_current_value(obj) - self.get_total_invested(obj)

    def get_profit_loss_percentage(self, obj):
        invested = self.get_total_invested(obj)
        if invested == 0:
            return 0
        return (self.get_profit_loss(obj) / invested) * 100

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value

    def validate_avg_buy_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Average buy price must be positive.")
        return value
        
class TransactionSerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.company_name', read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ('id', 'portfolio', 'stock', 'stock_symbol', 'stock_name',
                  'type', 'quantity', 'price', 'total_amount', 'timestamp')
        read_only_fields = ('id', 'portfolio', 'stock_symbol', 'stock_name',
                            'total_amount', 'timestamp')

    def get_total_amount(self, obj):
        return obj.quantity * obj.price

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

    def validate(self, data):
        if self.instance:
            raise serializers.ValidationError("Transaction cannot be modified once created.")

        if data.get('type') == 'SELL':
            portfolio = data.get('portfolio')
            stock = data.get('stock')
            quantity = data.get('quantity')

            if portfolio and stock:
                total_held = Holding.objects.filter(
                    portfolio=portfolio, stock=stock
                ).aggregate(total=models.Sum('quantity'))['total'] or 0

                if quantity > total_held:
                    raise serializers.ValidationError(
                        f"Cannot sell {quantity} shares. Only {total_held} available."
                    )
        return data