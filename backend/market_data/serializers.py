from rest_framework import serializers
from .models import Stock

class StockSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ('id', 'symbol', 'company_name', 'sector')
        
class StockSerializer(serializers.ModelSerializer):
    current_price = serializers.SerializerMethodField()
    day_change = serializers.SerializerMethodField()
    day_change_percentage = serializers.SerializerMethodField()
    is_in_user_portfolio = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = (
            'id', 'symbol', 'company_name', 'sector',
            'current_price', 'day_change', 'day_change_percentage',
            'is_in_user_portfolio', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_current_price(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'stock_service'):
            return request.stock_service.get_current_price(obj.symbol)
        return None

    def get_day_change(self, obj):
        return self.context.get('stock_service', {}).get('current_price', None)

    def get_day_change_percentage(self, obj):
        return self.context.get('stock_service', {}).get('price_change_percentage', None)

    def get_is_in_user_portfolio(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.holding.filter(portfolio__user=request.user).exists()
        return False

    def validate_symbol(self, value):
        value = value.upper().strip()
        if len(value) > 10:
            raise serializers.ValidationError("Stock symbol cannot exceed 10 characters.")
        return value


    def validate_company_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Company name must be at least 2 characters.")
        return value.strip()
        
class StockDetailSerializer(StockSerializer):
    market_cap = serializers.SerializerMethodField()
    pe_ratio = serializers.SerializerMethodField()
    volume = serializers.SerializerMethodField()
    day_high = serializers.SerializerMethodField()
    day_low = serializers.SerializerMethodField()
    year_high = serializers.SerializerMethodField()
    year_low = serializers.SerializerMethodField()

    class Meta(StockSerializer.Meta):
        fields = StockSerializer.Meta.fields + (
            'market_cap', 'pe_ratio', 'volume', 'day_high', 'day_low',
            'year_high', 'year_low'
            )

    def get_market_cap(self, obj):
        return self.context.get('stock_service', {}).get('market_cap', None)
    
    def get_pe_ratio(self, obj):
        return self.context.get('stock_service', {}).get('pe_ratio', None)
    
    def get_volume(self, obj):
        return self.context.get('stock_service', {}).get('volume', None)
    
    def get_day_high(self, obj):
        return self.context.get('stock_service', {}).get('day_high', None)
    
    def get_day_low(self, obj):
        return self.context.get('stock_service', {}).get('day_low', None)
    
    def get_year_high(self, obj):
        return self.context.get('stock_service', {}).get('year_high', None)
    
    def get_year_low(self, obj):
        return self.context.get('stock_service', {}).get('year_low', None)

class StockCreateUpdateSerializer(serializers.ModelSerializer):
    """To be used by admin only"""

    class Meta:
        model = Stock
        fields = ('symbol', 'company_name', 'sector')

    def create(self, validated_data):
        validated_data['symbol'] = validated_data['symbol'].upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'symbol' in validated_data:
            validated_data['symbol'] = validated_data['symbol'].upper()
        return super().update(instance, validated_data)

class HistoricalDataSerializer(serializers.Serializer):
    date = serializers.DateField()
    open = serializers.DecimalField(max_digits=10, decimal_places=2)
    high = serializers.DecimalField(max_digits=10, decimal_places=2)
    low = serializers.DecimalField(max_digits=10, decimal_places=2)
    close = serializers.DecimalField(max_digits=10, decimal_places=2)
    volume = serializers.IntegerField()

    class Meta:
        fields = ('date','open', 'high', 'low', 'close', 'volume')