from django.db import models
from users.models import CustomUser
from market_data.models import Stock

class Portfolio(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.email})"

class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='holdings')
    quantity = models.FloatField()
    avg_buy_price = models.FloatField()

    def __str__(self):
        return f"{self.stock.symbol} in {self.portfolio.name}"

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

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Transactions"