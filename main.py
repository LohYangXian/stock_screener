import pandas_datareader as web
import pandas as pd
import yfinance as yf
import datetime as dt

# Script to retrieve all the tickers from the S&P 500, get their data, and calculate their moving averages, then compare them to the S&P 500, and return the best performing stocks in a csv file 

# We can get a list of all the tickers from the S&P 500
tickers = pd.read_html(
    'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0].Symbol.to_list()

# Set start and end date
start = dt.datetime.now() - dt.timedelta(days=365)
end = dt.datetime.now()

# Get the data for ticker S&P 500
sp500_df = yf.download(tickers = '^GSPC', start=start, end=end)

sp500_df['Pct_Change'] = sp500_df['Adj Close'].pct_change()
# Calculate the cumulative return
sp500_return = (sp500_df['Pct_Change'] + 1).cumprod().iloc[-1]


return_list = []

# Add whatever metrics you are interested in to the list
final_df = pd.DataFrame(columns=['Ticker', 'Latest_Price', 'Score', 'PE_Ratio', 'PEG_Ratio', 'SMA_150', 'SMA_200', '52_Week_Low', '52_Week_High'])


for ticker in tickers:
    try:
        df = yf.download(tickers=ticker, start= start, end=end)
        # Saves the data for each ticker to a csv

        df.to_csv(f'stock_data/{ticker}.csv')

        df['Pct Change'] = df['Adj Close'].pct_change()
        stock_return = (df['Pct Change'] + 1).cumprod().iloc[-1]

        returns_compared = round((stock_return / sp500_return), 2)
        return_list.append(returns_compared)
    except Exception as e:
        print(f"{e} for ticker: {ticker}")
    



best_performers = pd.DataFrame(list(zip(tickers, return_list)), columns=['Ticker', 'Returns Compared'])
best_performers['Score'] = best_performers['Returns Compared'].rank(pct=True) * 100

# Get the best performing stocks by return
best_performers = best_performers[best_performers['Score'] >= best_performers['Score'].quantile(0.7)]

for ticker in best_performers['Ticker']:
    try:
        df = pd.read_csv(f'stock_data/{ticker}.csv', index_col=0)
        # Calculate moving averages
        moving_averages = [150,200]
        for ma in moving_averages:
            df['SMA_' + str(ma)] = round(df['Adj Close'].rolling(window=ma).mean(), 2)

        latest_price = df['Adj Close'].iloc[-1]
        
        ticker_info = yf.Ticker(ticker).info
        # The PE ratio (P/E ratio) is a valuation metric for determining the price of a stock relative to its earnings per share.
        pe_ratio = float(ticker_info["trailingPE"]) if ticker_info["trailingPE"] is not None else 0

        # The PEG ratio (Price/Earnings to Growth ratio) is a valuation metric for determining the relative trade-off between the price of a stock, the earnings generated per share (EPS), and the company's expected growth.
        peg_ratio = float(ticker_info["pegRatio"]) if ticker_info["pegRatio"] is not None else 0

        moving_average_150 = df['SMA_150'].iloc[-1]
        moving_average_200 = df['SMA_200'].iloc[-1]
        
        # We use 52 * 5 because theres 5 days in a week
        low_52_week = round(min(df['Low'][-(52*5):]), 2)
        high_52_week = round(max(df['High'][-(52*5):]), 2)
        score = round(best_performers[best_performers['Ticker'] == ticker]['Score'].tolist()[0], 2)

        # Set Conditions for Stock Screener
        condition_1 = latest_price > moving_average_150 > moving_average_200
        condition_2 = latest_price >= (1.3 * low_52_week)
        condition_3 = latest_price >= (0.75 * high_52_week)
        condition_4 = pe_ratio < 40
        condition_5 = peg_ratio < 2

        if condition_1 and condition_2 and condition_3 and condition_4 and condition_5:
        # Note that append has been removed from pandas so we need to use _append
            final_df = final_df._append({'Ticker': ticker,
                                        'Latest_Price': latest_price,
                                        'Score': score,
                                        'PE_Ratio': pe_ratio,
                                        'PEG_Ratio': peg_ratio,
                                        'SMA_150': moving_average_150,
                                        'SMA_200': moving_average_200,
                                        '52_Week_Low': low_52_week,
                                        '52_Week_High': high_52_week}, ignore_index=True)

    except Exception as e:
        print(f"{e} for ticker: {ticker}")

final_df.sort_values(by='Score', ascending=False)
pd.set_option('display.max_columns', 10)
print(final_df)
final_df.to_csv('stock_screener.csv')
