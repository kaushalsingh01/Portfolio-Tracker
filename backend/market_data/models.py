from django.db import models

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True, blank=False, null=False)
    company_name = models.CharField(max_length=100, blank=False, null=False)
    sector = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.company_name}"

    class Meta:
        verbose_name_plural = "Stocks"