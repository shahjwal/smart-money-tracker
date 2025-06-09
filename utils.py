import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

class StockDataFetcher:
    def __init__(self):
        # Popular stocks to monitor
        self.watchlist = ['AAPL', 'TSLA', 'MSFT', 'NVDA', 'GOOGL', 'META', 'AMZN', 'SPY', 'QQQ', 'AMD']
        
    def get_stock_data(self, symbol):
        """Get current stock data and options chain"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current price
            info = ticker.info
            current_price = info.get('currentPrice', 0)
            
            # If currentPrice not available, try regularMarketPrice
            if current_price == 0:
                current_price = info.get('regularMarketPrice', 0)
            
            # Get options chain
            options_dates = ticker.options
            
            if len(options_dates) > 0:
                # Get the nearest expiration date
                nearest_expiry = options_dates[0]
                options_chain = ticker.option_chain(nearest_expiry)
                
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'company_name': info.get('longName', symbol),
                    'options_chain': options_chain,
                    'expiry_date': nearest_expiry,
                    'info': info
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def detect_unusual_options_activity(self, symbol):
        """Detect unusual options activity for a symbol"""
        try:
            data = self.get_stock_data(symbol)
            if not data or 'options_chain' not in data:
                return None
            
            calls = data['options_chain'].calls
            puts = data['options_chain'].puts
            
            # Calculate unusual activity for calls
            unusual_calls = self._find_unusual_volume(calls, 'CALL')
            unusual_puts = self._find_unusual_volume(puts, 'PUT')
            
            # Combine and sort by volume ratio
            all_unusual = unusual_calls + unusual_puts
            all_unusual.sort(key=lambda x: x['volume_ratio'], reverse=True)
            
            # Add current price to each alert
            for alert in all_unusual:
                alert['current_price'] = data['current_price']
                alert['company_name'] = data['company_name']
            
            return all_unusual[:5]  # Return top 5 unusual activities
            
        except Exception as e:
            print(f"Error detecting unusual activity for {symbol}: {str(e)}")
            return []
    
    def _find_unusual_volume(self, options_df, option_type):
        """Find options with unusual volume"""
        unusual = []
        
        for _, row in options_df.iterrows():
            volume = row.get('volume', 0)
            open_interest = row.get('openInterest', 0)
            
            # Skip if no volume
            if pd.isna(volume) or volume == 0:
                continue
            
            # Calculate volume to open interest ratio
            if open_interest > 0:
                vol_oi_ratio = volume / open_interest
            else:
                vol_oi_ratio = volume
            
            # Consider unusual if volume is high relative to open interest
            if vol_oi_ratio > 0.5 or volume > 1000:
                strike = row['strike']
                last_price = row.get('lastPrice', 0)
                
                # Estimate premium spent
                premium_spent = volume * last_price * 100  # Each contract is 100 shares
                
                # Only include if significant premium
                if premium_spent > 50000:  # $50k minimum
                    unusual.append({
                        'symbol': row.get('contractSymbol', ''),
                        'strike': strike,
                        'option_type': option_type,
                        'volume': int(volume),
                        'open_interest': int(open_interest) if open_interest else 0,
                        'volume_ratio': round(vol_oi_ratio, 2),
                        'last_price': last_price,
                        'premium': premium_spent,
                        'implied_volatility': row.get('impliedVolatility', 0)
                    })
        
        return unusual
    
    def scan_all_watchlist(self):
        """Scan all watchlist stocks for unusual activity"""
        all_alerts = []
        
        for symbol in self.watchlist:
            print(f"Scanning {symbol}...")
            unusual = self.detect_unusual_options_activity(symbol)
            
            if unusual:
                for activity in unusual:
                    activity['symbol'] = symbol
                    all_alerts.append(activity)
        
        # Sort by premium spent
        all_alerts.sort(key=lambda x: x['premium'], reverse=True)
        
        return all_alerts
    
    def get_market_sentiment(self):
        """Calculate overall market sentiment based on put/call ratios"""
        try:
            spy = yf.Ticker('SPY')
            options_dates = spy.options
            
            if len(options_dates) > 0:
                options_chain = spy.option_chain(options_dates[0])
                
                total_call_volume = options_chain.calls['volume'].sum()
                total_put_volume = options_chain.puts['volume'].sum()
                
                if total_call_volume > 0:
                    put_call_ratio = total_put_volume / total_call_volume
                else:
                    put_call_ratio = 0
                
                # Sentiment score (0-100)
                # Lower put/call ratio = more bullish
                # Higher put/call ratio = more bearish
                if put_call_ratio < 0.7:
                    sentiment_score = 80 + (0.7 - put_call_ratio) * 20
                elif put_call_ratio > 1.3:
                    sentiment_score = 20 - (put_call_ratio - 1.3) * 10
                else:
                    sentiment_score = 50
                
                sentiment_score = max(0, min(100, sentiment_score))
                
                return {
                    'put_call_ratio': round(put_call_ratio, 3),
                    'sentiment_score': round(sentiment_score, 1),
                    'total_call_volume': int(total_call_volume),
                    'total_put_volume': int(total_put_volume),
                    'sentiment_text': self._get_sentiment_text(sentiment_score)
                }
            
        except Exception as e:
            print(f"Error calculating sentiment: {str(e)}")
            
        return {
            'put_call_ratio': 1.0,
            'sentiment_score': 50,
            'total_call_volume': 0,
            'total_put_volume': 0,
            'sentiment_text': 'Neutral'
        }
    
    def _get_sentiment_text(self, score):
        """Convert sentiment score to text"""
        if score >= 80:
            return "Extreme Greed"
        elif score >= 65:
            return "Greed"
        elif score >= 50:
            return "Neutral"
        elif score >= 35:
            return "Fear"
        else:
            return "Extreme Fear"
    
    def get_historical_performance(self, symbol, days=30):
        """Get historical price data for performance tracking"""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty:
                return hist
            
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
        
        return pd.DataFrame()

# Helper function to format large numbers
def format_number(num):
    """Format large numbers with K, M, B suffixes"""
    if num >= 1e9:
        return f"${num/1e9:.1f}B"
    elif num >= 1e6:
        return f"${num/1e6:.1f}M"
    elif num >= 1e3:
        return f"${num/1e3:.1f}K"
    else:
        return f"${num:.0f}"