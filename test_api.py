import yfinance as yf

# Test basic functionality
ticker = yf.Ticker("AAPL")
info = ticker.info
print("Current Price:", info.get('currentPrice', 'Not found'))
print("Company Name:", info.get('longName', 'Not found'))

# Test options
options_dates = ticker.options
print("Options dates available:", len(options_dates))
if len(options_dates) > 0:
    print("First expiry:", options_dates[0])