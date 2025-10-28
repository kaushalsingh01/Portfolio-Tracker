from rest_framework import serializers
from .models import Stock

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
        # Placeholder for actual logic
        return None

    def get_day_change_percentage(self, obj):
        # Placeholder for actual logic
        return None

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

    class Meta(StockSerializer.Meta):
        fields = StockSerializer.Meta.fields + ('market_cap', 'pe_ratio')

    def get_market_cap(self, obj):
        return None  # Placeholder

    def get_pe_ratio(self, obj):
        return None  # Placeholder

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