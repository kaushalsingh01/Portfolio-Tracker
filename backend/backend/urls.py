# main urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# Import views from respective apps
from portfolio.views import PortfolioViewset
from users.views import AuthViewSet
from market_data.views import StockViewSet, StockSearchViewset

# Import analysis views (make sure these exist in your analysis app)
from analysis.views import (
    PortfolioAnalysisViewSet,
    PortfolioPredictionViewSet, 
    StockPredictionViewSet,
    SentimentAnalysisViewSet,
    ModelManagementViewSet,
    SystemHealthViewSet,
    CombinedAnalysisViewSet
)


router = DefaultRouter()

# Core app endpoints
router.register(r'portfolios', PortfolioViewset, basename='portfolio')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'stocks', StockViewSet, basename='stock')
router.register(r'search', StockSearchViewset, basename='stock-search')

# Analysis endpoints
router.register(r'portfolio-analysis', PortfolioAnalysisViewSet, basename='portfolio-analysis')
router.register(r'portfolio-predictions', PortfolioPredictionViewSet, basename='portfolio-predictions')
router.register(r'predictions', StockPredictionViewSet, basename='stock-predictions')
router.register(r'sentiment', SentimentAnalysisViewSet, basename='sentiment-analysis')
router.register(r'model-management', ModelManagementViewSet, basename='model-management')
router.register(r'health', SystemHealthViewSet, basename='system-health')
router.register(r'combined-analysis', CombinedAnalysisViewSet, basename='combined-analysis')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

