import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ASX tickers (Yahoo requires .AX suffix)
tickers = ["AAA.AX", "VAS.AX", "VTS.AX", "SOL.AX"]

# Last 12 months
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

all_data = []

for ticker in tickers:
    stock = yf.Ticker(ticker)
    dividends = stock.dividends

    if dividends.empty:
        continue

  # Remove timezone for comparison
dividends.index = dividends.index.tz_localize(None)

dividends = dividends[
    (dividends.index >= start_date) &
    (dividends.index <= end_date)
]

    for date, amount in dividends.items():
        all_data.append({
            "Ticker": ticker.replace(".AX", ""),
            "Ex-Date": date.date(),
            "Dividend per Share": round(amount, 6)
        })

df = pd.DataFrame(all_data)

if not df.empty:
    df = df.sort_values(by=["Ex-Date", "Ticker"])

filename = f"Dividend_Report_{end_date.strftime('%b_%Y')}.xlsx"
df.to_excel(filename, index=False)

print(f"File created: {filename}")
