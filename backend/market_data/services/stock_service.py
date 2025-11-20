import yfinance as yf
import requests
from ..models import Stock

class StockService:
    ALPHA_VANTAGE_API_KEY = '2RR0BFP2CP2N9FL9'
    @staticmethod
    def get_real_time_quote(symbol):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info:
                data = {
                    'current_price': info.get('currentPrice'),
                    'price_change': info.get('regularMarketChange'),
                    'price_change_percentage': info.get('regularMarketChangePercent'),
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'volume': info.get('volume'),
                    'day_high': info.get('dayHigh'),
                    'day_low': info.get('dayLow'),
                    'year_high': info.get('fiftyTwoWeekHigh'),
                    'year_low': info.get('fiftyTwoWeekLow')
                }
                return data
            else:
                print(f"No data available for {symbol}.")
                return None
        except Exception as e:
            print(f"Unable to fetch data for {symbol}. Error: {e}")
            return None

    @staticmethod
    def get_historical_data(symbol, period='1mo', interval='1d'):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            historical_data = []
            if not hist.empty:
                for date, row in hist.iterrows():
                    data = {
                        'date': date.strftime('%Y-%m-%d'),
                        'open': row['Open'],
                        'high': row['High'],
                        'low': row['Low'],
                        'close': row['Close'],
                        'volume': row['Volume']
                    }
                    historical_data.append(data)
                return historical_data
            else:
                print(f"No historical data available for {symbol}.")
                return None
        except Exception as e:
            print(f"Unable to fetch historical data for {symbol}. Error: {e}")
            return None
    @staticmethod
    def search_stocks(query):
        url = f'https://www.alphavantage.co/query'
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query,
            'apikey': StockService.ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get('bestMatches', [])
            return [
                {
                    'symbol': match['1. symbol'],
                    'company_name': match['2. name'],
                    'region': match['4. region'],
                    'currency': match['8. currency']
                }
                for match in results
            ]
        else:
            print(f"API error: {response.status_code}")
            return []
    @staticmethod
    def sync_stock_data(symbol):
        try:
            quote_data = StockService.get_real_time_quote(symbol)
            if not quote_data:
                raise ValueError("No quote data returned")
            company_name = quote_data.get('company_name') or f"Company for {symbol}"
            sector = quote_data.get('sector') or 'Unknown'
            stock, created = Stock.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'company_name':company_name,
                    'sector': sector,
                }
            )
            return stock
        except Exception as e:
            print(f"Error syncing stock data for {symbol}: {str(e)}")
            return None


# if __name__ == "__main__":
#     results = StockService.search_stocks("apple")
#     print("Search results for 'apple':")
#     for stock in results:
#         print(stock)
# #  Example usage
#     rt_data = StockService.get_real_time_quote("MSFT")
#     print(f"MSFT real-time data: {rt_data}")

#     ht_data = StockService.get_historical_data("MSFT")
#     print(f"MSFT historical data: {ht_data}")