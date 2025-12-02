# test_news_sentiment.py
from news_analyzer import NewsSentimentAnalyzer  # save your class in news_sentiment_analyzer.py

def main():
    # Initialize analyzer
    analyzer = NewsSentimentAnalyzer()

    # Optionally set your NewsAPI key here if you have one
    analyzer.news_api_key = "3149958826544cad9630f9a8b861f498"  # replace with real key or leave as "APIKEY"

    # Test with Apple stock
    result = analyzer.get_stock_sentiment(symbol="AAPL", company_name="Apple Inc")

    # Print overall sentiment
    print("Symbol:", result['symbol'])
    print("Overall Sentiment:", result['overall_sentiment'])
    print("Sentiment Score:", result['sentiment_score'])
    print("Confidence:", result['confidence'])
    print("Articles Analyzed:", result['article_count'])

    # Print details of first few articles
    print("\nSample Articles:")
    for article in result['articles']:
        print(f"- {article['title']} ({article['sentiment']}, confidence={article['confidence']:.2f})")

if __name__ == "__main__":
    main()