from django.contrib import admin
from .models import Stock

class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company_name', 'sector', 'created_at', 'updated_at')
    search_fields = ('symbol', 'company_name', 'sector')
    list_filter = ('sector', 'created_at')

admin.site.register(Stock, StockAdmin)