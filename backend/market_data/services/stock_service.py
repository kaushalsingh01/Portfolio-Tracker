import yfinance as yf

class StockService:
    @staticmethod
    def get_current_price(symbol):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                return current_price
            else:
                print(f"No historical data available for {symbol}.")
                return None
        except Exception as e:
            print(f"Unable to fetch current price for {symbol}. Error: {e}")
            return None

# price = StockService.get_current_price("I")
# print(f"AAPL current price: {price}")