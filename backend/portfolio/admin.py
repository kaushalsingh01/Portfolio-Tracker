from django.contrib import admin
from .models import Portfolio, Holding

class HoldingInline(admin.TabularInline):
    model = Holding
    extra = 1

class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'updated_at')
    search_fields = ('name', 'user__email')
    list_filter = ('created_at',)
    inlines = [HoldingInline]

class HoldingAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'stock', 'quantity', 'avg_buy_price')
    search_fields = ('portfolio__name', 'stock__symbol')
    list_filter = ('portfolio', 'stock')

admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(Holding, HoldingAdmin)