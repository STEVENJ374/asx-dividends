import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time

# ------------- CONFIG -------------

tickers = [
    "AAA.AX","AIA.AX","ANN.AX","APE.AX","ASK.AX","BHP.AX",
    "CIP.AX","CLW.AX","CNU.AX","CSL.AX","EDV.AX","EQT.AX",
    "EVT.AX","HCW.AX","IFT.AX","INIF.AX","IOO.AX","IOZ.AX",
    "IVV.AX","MIN.AX","NSR.AX","RMD.AX","SHL.AX","STW.AX",
    "TLC.AX","TLS.AX","VAS.AX","VGS.AX","VTS.AX","WOW.AX",
    "WPR.AX","COL.AX","VEU.AX","VHY.AX"
]

end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# ----------------------------------

def get_investsmart_data(ticker, ex_date):
    """
    Scrape InvestSMART dividend table for matching ex-date.
    If not found or layout issue, return (None, None)
    """
    try:
        base = ticker.replace(".AX", "").lower()
        url = f"https://www.investsmart.com.au/shares/asx-{base}/dividends"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None, None

        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = [c.get_text(strip=True) for c in row.find_all("td")]

                if len(cols) < 4:
                    continue

                # Typical structure:
                # Ex Date | Pay Date | Dividend | Franking
                try:
                    row_ex_date = pd.to_datetime(cols[0], dayfirst=True).date()
                except:
                    continue

                if row_ex_date == ex_date:
                    pay_date = cols[1]
                    franking = cols[-1].replace("%", "").strip()

                    try:
                        franking = float(franking)
                    except:
                        franking = None

                    return pay_date, franking

        return None, None

    except:
        return None, None


all_data = []

for ticker in tickers:
    stock = yf.Ticker(ticker)
    dividends = stock.dividends

    if dividends.empty:
        continue

    dividends.index = dividends.index.tz_localize(None)

    dividends = dividends[
        (dividends.index >= start_date) &
        (dividends.index <= end_date)
    ]

    for date, amount in dividends.items():
        ex_date = date.date()

        pay_date, franking = get_investsmart_data(ticker, ex_date)

        all_data.append({
            "Ticker": ticker.replace(".AX", ""),
            "Ex-Date": ex_date,
            "Payment Date": pay_date,
            "Dividend per Share": round(amount, 6),
            "Franking %": franking
        })

    time.sleep(1)  # avoid rate limiting


df = pd.DataFrame(all_data)

if not df.empty:
    df = df.sort_values(by=["Ex-Date", "Ticker"])

filename = f"Dividend_Report_Extended_{end_date.strftime('%b_%Y')}.xlsx"
df.to_excel(filename, index=False)

print(f"File created: {filename}")
