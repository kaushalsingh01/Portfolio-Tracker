from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from portfolio.views import PortfolioViewset
from market_data.views import StockViewSet, StockSearchViewset
from users.views import AuthViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'portfolios', PortfolioViewset, basename='portfolio')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'stocks', StockViewSet, basename='stock')
router.register(r'search', StockSearchViewset, basename='stock-search')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
