
from price_predictor import StockPricePredictor  # assuming you saved your class in stock_predictor.py

# Initialize
predictor = StockPricePredictor()

# Train on Apple stock
trained = predictor.train_model("MSFT")

if trained:
    print("Model trained and saved successfully.")

    # Predict next 7 days
    future_prices = predictor.predict_future("MSFT", days=7)
    print("Future predictions:", future_prices)

    # Get trading signal
    signal = predictor.get_trading_signal("MSFT")
    print("Trading signal:", signal)
else:
    print("Training failed.")