import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class NewsSentimentAnalyzer:
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.news_api_key = "3149958826544cad9630f9a8b861f498"
        
    def fetch_news(self, symbol, company_name=None, days=7):
        """Fetch recent news for a stock"""
        try:
            # Calculate date range
            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Search using company name and symbol
            query = f"{symbol} {company_name}" if company_name else symbol
            url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&apiKey={self.news_api_key}"
            
            response = requests.get(url)
            articles = response.json().get('articles', [])
            
            return articles[:20]  # Return top 20 articles
            
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            # Fallback to mock data
            return self._get_mock_news(symbol)
    
    def _get_mock_news(self, symbol):
        """Mock news data for development"""
        mock_articles = [
            {
                'title': f"{symbol} shows strong quarterly results",
                'description': f"Company {symbol} reported better than expected earnings",
                'publishedAt': datetime.now().isoformat(),
                'url': '#',
                'source': {'name': 'Financial News'}
            },
            {
                'title': f"Analysts bullish on {symbol} future prospects",
                'description': f"Market analysts recommend buying {symbol} stock",
                'publishedAt': (datetime.now() - timedelta(days=1)).isoformat(),
                'url': '#', 
                'source': {'name': 'Market Watch'}
            }
        ]
        return mock_articles
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text using multiple methods"""
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        # VADER sentiment
        vader_scores = self.vader_analyzer.polarity_scores(text)
        
        # Combined score (weighted average)
        combined_score = (textblob_polarity + vader_scores['compound']) / 2
        
        return {
            'textblob_polarity': textblob_polarity,
            'textblob_subjectivity': textblob_subjectivity,
            'vader_compound': vader_scores['compound'],
            'vader_positive': vader_scores['pos'],
            'vader_negative': vader_scores['neg'],
            'vader_neutral': vader_scores['neu'],
            'combined_score': combined_score
        }
    
    def get_stock_sentiment(self, symbol, company_name=None):
        """Get overall sentiment for a stock"""
        articles = self.fetch_news(symbol, company_name)
        
        if not articles:
            return {
                'symbol': symbol,
                'overall_sentiment': 'NEUTRAL',
                'confidence': 0.5,
                'article_count': 0,
                'articles': []
            }
        
        analyzed_articles = []
        sentiment_scores = []
        
        for article in articles:
            # Combine title and description for analysis
            text = f"{article['title']}. {article.get('description', '')}"
            sentiment = self.analyze_sentiment(text)
            
            # Determine sentiment label
            if sentiment['combined_score'] > 0.1:
                sentiment_label = 'POSITIVE'
            elif sentiment['combined_score'] < -0.1:
                sentiment_label = 'NEGATIVE'
            else:
                sentiment_label = 'NEUTRAL'
            
            analyzed_articles.append({
                'title': article['title'],
                'description': article.get('description', ''),
                'source': article['source']['name'],
                'published_at': article['publishedAt'],
                'sentiment': sentiment_label,
                'confidence': abs(sentiment['combined_score']),
                'url': article['url']
            })
            
            sentiment_scores.append(sentiment['combined_score'])
        
        # Calculate overall sentiment
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        confidence = min(abs(avg_sentiment) * 2, 1.0)  
        
        if avg_sentiment > 0.1:
            overall_sentiment = 'BULLISH'
        elif avg_sentiment < -0.1:
            overall_sentiment = 'BEARISH'
        else:
            overall_sentiment = 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'overall_sentiment': overall_sentiment,
            'sentiment_score': avg_sentiment,
            'confidence': confidence,
            'article_count': len(articles),
            'articles': analyzed_articles[:5]
        }