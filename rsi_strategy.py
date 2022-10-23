# Finds the probability of each trading condition
import csv
import os
import pandas as pd


def above_200ma_10days(candles, index):
    for i in range(index - 10, index):
        candle = candles[i]
        candle_200ma = float(candle['200MA'])
        candle_low = float(candle['Low'])

        if candle_low <= candle_200ma:
            return False
    return True


def buy_price(candles, index):
    current_candle = candles[index]
    previous_candle = candles[index - 1]
    current_open = float(current_candle['Open'])
    previous_rsi10 = float(previous_candle['rsi_10'])

    if above_200ma_10days(candles, index) and previous_rsi10 < 30:
        return current_open
    return False


def print_trade_summary(df):
    total_trades = df.shape[0]
    total_wins = (df['Profit'] > 0).sum()
    total_losses = total_trades - total_wins
    pc_wins = round(total_wins / total_trades * 100, 2)
    pc_losses = 100 - pc_wins
    avg_profit = df['Profit'].mean()
    std = df['Profit'].std()

    avg_win = (df[df['Profit'] > 0]['Profit']).mean()
    avg_loss = (df[df['Profit'] <= 0]['Profit']).mean()


    print(f'Total trades: {total_trades}')
    print(f'Mean profit %: {avg_profit}%')
    print(f'Std: {std}')
    print()

    print('WINS')
    print(f'Total: {total_wins}')
    print(f'%: {pc_wins}')
    print(f'Mean win %: {avg_win}')
    print()
    print('LOSSES')
    print(f'Total: {total_losses}')
    print(f'%: {pc_losses}')
    print(f'Mean loss %: {avg_loss}')


def sell_price(current_candle, previous_candle, position):
    purchase_index = position['Index']
    current_open = float(current_candle['Open'])
    rsi = float(previous_candle['rsi_10'])
    current_low = float(current_candle['Low'])

    if current_open < rsi > 40 or index - purchase_index == 11:
        return current_open
    return False


def update_held_positions(current_candle, previous_candle, ticker):
    position = dict()
    features = ['Date', 'Open', 'Close', '20ATR', 'rsi_10']
    for feature in features:
        position[feature] = previous_candle[feature]

    position['Purchase'] = buy_price(candles, index)
    position['Ticker'] = ticker
    position['Index'] = index
    held_positions.append(position)


this_fp = os.path.realpath(__file__)
history_dir = os.path.dirname(this_fp) + '\\history'
df = pd.DataFrame()

for f in os.listdir(history_dir):
    if not f.endswith('.csv'):
        continue

    ticker = f.split('.')[0]
    file_dir = history_dir + '\\' + f
    candles = list(csv.DictReader(open(file_dir)))
    held_positions = []
    potential_buy = False

    for index in range(20, len(candles)): # 10 as we check past 20 days are above 200ma before buying.
        current_candle = candles[index]
        previous_candle = candles[index - 1]

        # Look through held position for any exit conditions met.
        for position in held_positions.copy():
            # exit conditions met.
            if sell_price(current_candle, previous_candle, position):
                held_positions.remove(position)
                position['Sold'] = sell_price(current_candle, previous_candle, position)
                df = df.append(position, ignore_index=True)
                continue

        if len(held_positions) < 1 and buy_price(candles, index): 
        # Add new position to held_positions.
            update_held_positions(current_candle, previous_candle, ticker)

# Calculate profit.
df = df.astype('float64', errors='ignore')
df['Profit'] = (df['Sold'] - df['Purchase']) / df['Purchase'] * 100

df.to_csv('rsi_strategy_data.csv')
print('\n' * 2)
print_trade_summary(df)