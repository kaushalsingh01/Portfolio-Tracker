from django.db import models
from users.models import CustomUser
from market_data.models import Stock
from django.db.models import Sum, F
from decimal import Decimal

class Portfolio(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.email})"
    
    @property
    def total_invested(self):
        total = self.holdings.aggregate(
            total=Sum(F('quantity') * F('avg_buy_price'))
        )['total']
        return total or Decimal('0.00')
    
    @property
    def holdings_count(self):
        return self.holdings.count()
    
    def get_current_value(self):
        total_value = Decimal('0.00')
        for holding in self.holdings.all():
            from market_data.services.stock_service  import StockService
            current_price = StockService.get_current_price(holding.stock.symbol)
            total_value += holding.quantity * Decimal(str(current_price))
        return total_value

class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='holdings')
    quantity = models.FloatField()
    avg_buy_price = models.FloatField()

    def __str__(self):
        return f"{self.stock.symbol} in {self.portfolio.name}"
    
    @property
    def total_invested(self):
        return self.quantity * self.avg_buy_price
    
    def get_current_value(self):
        from market_data.services import StockService
        current_price = StockService.get_current_price(self.stock.symbol)
        return self.quantity * Decimal(str(current_price))
    
    def get_profit_loss(self):
        current_value = self.get_current_value()
        invested = Decimal(str(self.total_invested))
        return current_value - invested
    
    def get_profit_loss_percentage(self):
        invested = Decimal(str(self.total_invested))
        if invested > 0:
            return (self.get_profit_loss() / invested) * 100
        return Decimal('0.00')

class Transaction(models.Model):
    TYPE = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="transactions")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="transactions")
    type = models.CharField(max_length=4, choices=TYPE)
    quantity = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} {self.quantity} {self.stock.symbol} @ {self.price} ({self.portfolio.name})"
    
    @property
    def total_amount(self):
        return self.quantity * self.price

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Transactions"