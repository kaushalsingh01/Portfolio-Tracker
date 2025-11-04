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
    
class PortfolioListSerializer(serializers.ModelSerializer):
    holdings_count = serializers.IntegerField(read_only = True)

    class Meta:
        model = Portfolio
        fields = ('id', 'name', 'description', 'created_at', 'holdings_count')

class PortfolioDeatilSerializer(PortfolioSerializer):
    holding = HoldingSerializer(many=True, read_only=True)
    recent_transaction = serializers.SerializerMethodField()

    class Meta(PortfolioSerializer.Meta):
        fields = PortfolioSerializer.Meta.fields + ('holdings', 'recent_transactions')
    
    def get_recent_transactions(self, obj):
        recent_tx = obj.transactions.all()[:5]
        return TransactionSerializer(recent_tx, many=True).data
    
class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('portfolio', 'stock', 'type', 'quantity', 'price')
    
    def create(self, validated_data):
        # Create the transaction first
        transaction = super().create(validated_data)
        
        # Update holdings based on FIFO logic
        self.update_holdings_with_fifo(transaction)
        
        return transaction
    
    def update_holdings_with_fifo(self, transaction):
        if transaction.type == 'BUY':
            self._handle_buy_transaction(transaction)
        else:  # SELL
            self._handle_sell_transaction_fifo(transaction)
    
    def _handle_buy_transaction(self, transaction):
        """Handle BUY transactions - create or update holding"""
        holding, created = Holding.objects.get_or_create(
            portfolio=transaction.portfolio,
            stock=transaction.stock,
            defaults={
                'quantity': transaction.quantity,
                'avg_buy_price': transaction.price
            }
        )
        
        if not created:
            # Update existing holding with new average price
            total_quantity = holding.quantity + transaction.quantity
            total_value = (holding.quantity * holding.avg_buy_price) + \
                         (transaction.quantity * transaction.price)
            
            holding.quantity = total_quantity
            holding.avg_buy_price = total_value / total_quantity
            holding.save()
    
    def _handle_sell_transaction_fifo(self, transaction):
        """Handle SELL transactions using FIFO method"""
        from django.db import models
        from decimal import Decimal
        
        # Get all BUY transactions for this stock in FIFO order (oldest first)
        buy_transactions = Transaction.objects.filter(
            portfolio=transaction.portfolio,
            stock=transaction.stock,
            type='BUY',
            quantity__gt=0  # Only consider unsold shares
        ).order_by('timestamp')
        
        remaining_sell_qty = transaction.quantity
        total_cost_basis = Decimal('0.0')
        
        # Process each buy transaction in FIFO order
        for buy_tx in buy_transactions:
            if remaining_sell_qty <= 0:
                break
            
            # Determine how many shares to sell from this buy lot
            shares_to_sell_from_lot = min(remaining_sell_qty, buy_tx.quantity)
            
            # Calculate cost basis for these shares
            cost_basis_for_lot = shares_to_sell_from_lot * buy_tx.price
            total_cost_basis += cost_basis_for_lot
            
            # Reduce the quantity from this buy transaction
            buy_tx.quantity -= shares_to_sell_from_lot
            buy_tx.save()
            
            remaining_sell_qty -= shares_to_sell_from_lot
        
        # Update or remove the holding
        self._update_holding_after_sale(transaction, total_cost_basis)
        
        # Verify we sold exactly what we intended
        if remaining_sell_qty > 0:
            raise serializers.ValidationError(
                f"Insufficient shares. Could only sell {transaction.quantity - remaining_sell_qty} out of {transaction.quantity} shares."
            )
    
    def _update_holding_after_sale(self, transaction, total_cost_basis):
        """Update the holding record after a sale"""
        try:
            holding = Holding.objects.get(
                portfolio=transaction.portfolio,
                stock=transaction.stock
            )
            
            # Calculate remaining quantity
            remaining_quantity = holding.quantity - transaction.quantity
            
            if remaining_quantity <= 0:
                # Remove holding if no shares left
                holding.delete()
            else:
                # Update holding with remaining shares
                # Note: avg_buy_price remains the same for remaining shares
                holding.quantity = remaining_quantity
                holding.save()
                
        except Holding.DoesNotExist:
            # This shouldn't happen if validation is working, but handle gracefully
            raise serializers.ValidationError("No holding found for this stock.")