from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .serializers import StockSerializer, StockCreateUpdateSerializer, StockDetailSerializer, StockSearchSerializer
from .models import Stock
from rest_framework.permissions import IsAdminUser, AllowAny
# Create your views here.
class StockViewSet(ModelViewSet):
    serializer_class = StockSerializer
    queryset = Stock.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return StockCreateUpdateSerializer
        elif self.action == 'list':
            return StockSearchSerializer
        elif self.action == 'retrieve':
            return StockDetailSerializer
        return StockSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]