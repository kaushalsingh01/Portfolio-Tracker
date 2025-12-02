from analysis.services.prediction_service import PredictorService

service = PredictorService("AAPL")

future_prices = service.predict_future(days=7)
print("Future prices: ", future_prices)
signal = service.get_signal()
print("Trading signal:", signal)