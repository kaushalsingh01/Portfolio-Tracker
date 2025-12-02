from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce
from collections import defaultdict
from decimal import Decimal

class PortfolioAnalyzer:
    @staticmethod
    def analyze_portfolio(portfolio):
        return {
            'basic_metrics': PortfolioAnalyzer.get_basic_metric(portfolio),
            'sector_metrics': PortfolioAnalyzer.get_sector_metrics(portfolio),
            'performance_analysis': PortfolioAnalyzer.get_performance_analysis(portfolio),
            'holding_analysis': PortfolioAnalyzer.get_holding_analysis(portfolio)
        }

    @staticmethod
    def get_basic_metric(portfolio):
        total_invested = portfolio.total_invested
        current_value = portfolio.get_current_value()
        total_pl = current_value - total_invested
        total_pl_percentage = (total_pl / total_invested * 100) if total_invested > 0 else 0

        return {
            'total_invested': float(total_invested),
            'current_value': float(current_value),
            'total_profit_loss': float(total_pl),
            'total_profit_loss_percentage': float(total_pl_percentage),
            'holding_count': portfolio.holdings_count,
            'transaction_count': portfolio.transaction.count()
        }

    @staticmethod
    def get_sector_metrics(portfolio):
        holdings = portfolio.holdings.select_related("stock").all()
        sector_data = defaultdict(lambda: {'value': Decimal('0.00'), 'percentage': Decimal('0.00')})
        total_value = portfolio.get_current_value()

        for holding in holdings:
            sector = holding.stock.sector or 'Unknown'
            current_value = holding.get_current_value()
            sector_data[sector]['value'] += current_value

        if total_value > 0:
            for sector, data in sector_data.items():
                data['percentage'] = (data['value'] / total_value) * Decimal('100')

        return {
            sector: {
                'value': float(data['value']),
                'percentage': float(data['percentage'])
            }
            for sector, data in sector_data.items()
        }

    @staticmethod
    def get_performance_analysis(portfolio):
        holdings = portfolio.holdings.select_related("stock").all()
        performers = []
        for holding in holdings:
            performers.append({
                'symbol': holding.stock.symbol,
                'company_name': holding.stock.company_name,
                'quantity': holding.quantity,
                'avg_buy_price': holding.avg_buy_price,
                'current_value': float(holding.get_current_value()),
                'profit_loss': float(holding.get_profit_loss()),
                'profit_loss_percentage': float(holding.get_profit_loss_percentage())
            })

        top_performers = sorted(performers, key=lambda x: x['profit_loss_percentage'], reverse=True)[:5]
        bottom_performers = sorted(performers, key=lambda x: x['profit_loss_percentage'])[:5]

        return {
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,
            'all_holdings': performers
        }

    @staticmethod
    def get_holding_analysis(portfolio):
        holdings = portfolio.holdings.all()
        total_value = portfolio.get_current_value()
        if total_value == 0:
            return {'concentration_score': 0, 'diversification_level': 'HIGH'}

        concentration_sum = Decimal('0.00')
        for holding in holdings:
            holding_value = holding.get_current_value()
            concentration = (holding_value / total_value) ** 2
            concentration_sum += concentration

        concentration_score = float(concentration_sum * 100)

        if concentration_score > 50:
            diversification = 'LOW'
        elif concentration_score > 25:
            diversification = 'MEDIUM'
        else:
            diversification = 'HIGH'

        return {
            'concentration_score': concentration_score,
            'diversification_level': diversification,
            'recommendation': PortfolioAnalyzer.get_diversification_recommendation(diversification)
        }

    @staticmethod
    def get_diversification_recommendation(level):
        recommendations = {
            'LOW': 'Consider diversifying across more stocks and sectors',
            'MEDIUM': 'Good diversification, consider adding different sectors',
            'HIGH': 'Excellent diversification across your portfolio'
        }
        return recommendations.get(level, '')