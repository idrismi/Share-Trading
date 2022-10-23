import os
import pandas as pd
import yfinance as yf
import numpy as np


def rma(x, n, y0):
    # Code from Stef: https://stackoverflow.com/questions/57006437/calculate-rsi-indicator-from-pandas-dataframe/57037866
    a = (n-1) / n
    ak = a**np.arange(len(x)-1, -1, -1)
    return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a**np.arange(1, len(x)+1)]

def column_index_from_name(df, col_name):
    # Converts a columns name to its numerical index.
    columns = list(df.columns)
    return columns.index(col_name)

def true_range(df, index):
    # Calculates the True Range.
    current_high = df.iloc[index, column_index_from_name(df, 'High')]
    current_low = df.iloc[index, column_index_from_name(df, 'Low')]
    previous_close = df.iloc[index - 1, column_index_from_name(df, 'Close')]
    return max(
        (current_high - current_low),
        abs(current_high - previous_close),
        abs(current_low - previous_close)
        )


this_fp = os.path.realpath(__file__)
current_dir = os.path.dirname(this_fp)
history_dir = current_dir + '/history'

if not os.path.exists(history_dir):
    os.mkdir(history_dir)

# DL sp500 data
# TODO: Get data from website https://datahub.io/core/s-and-p-500-companies#data
proceed = False
companies = pd.read_csv(current_dir + '/sp500.csv')
for _, company in companies.iterrows():
    symbol = company[0]

    # Download company data.
    try:
    
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='20y')
    except:
        print(f'Failed to DL {symbol}.')
        continue

    # Don't download if not enough data.
    if len(df) <= 200:
        continue

    # Clean data.
    df.drop(['Volume', 'Dividends', 'Stock Splits'], axis=1, inplace=True)
    df.dropna(axis=0, inplace=True)
    
    # Add moving averages.
    for n in [3, 5, 10, 20, 50, 100, 200]:
        df['{}MA'.format(n)] = df['Close'].rolling(window=n).mean().round(5)

    # Add True Range and 20 period ATR.
    for i in range(1, len(df)):
        df.loc[df.index[i],'TR'] = true_range(df, i)
    df['20ATR'] = df['TR'].rolling(window=20).mean().round(5)

    # Add average volume.
    df['avg_volume'] = df['Volume'].rolling(window=10).mean().round(5)

    # RSI.
    # Code from Stef: https://stackoverflow.com/questions/57006437/calculate-rsi-indicator-from-pandas-dataframe/57037866
    n = 10
    df['change'] = df['Close'].diff()
    df['gain'] = df.change.mask(df.change < 0, 0.0)
    df['loss'] = -df.change.mask(df.change > 0, -0.0)
    df['avg_gain'] = rma(df.gain[n+1:].to_numpy(), n, np.nansum(df.gain.to_numpy()[:n+1])/n)
    df['avg_loss'] = rma(df.loss[n+1:].to_numpy(), n, np.nansum(df.loss.to_numpy()[:n+1])/n)
    df['rs'] = df.avg_gain / df.avg_loss
    df['rsi_10'] = 100 - (100 / (1 + df.rs))

    # Clean and save.
    df.dropna(axis=0, inplace=True)
    df.to_csv(history_dir + '/{}.csv'.format(symbol))
    print('{} data saved.'.format(symbol))

print('\n\nDownload complete!')