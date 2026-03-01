import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time
import re

# -------- CONFIG --------

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

# ------------------------

def get_asx_dividend_data(ticker):
    """
    Conservative ASX HTML-only parsing.
    Skips PDF-only announcements.
    """

    try:
        code = ticker.replace(".AX", "")
        url = f"https://www.asx.com.au/asx/v2/statistics/announcements.do?by=asxCode&asxCode={code}"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)

        dividend_records = []

        for link in links:
            text = link.get_text(strip=True)

            if "Appendix 3A.1" in text or "Dividend" in text:

                ann_url = "https://www.asx.com.au" + link["href"]
                ann_resp = requests.get(ann_url, headers=headers, timeout=10)

                if ann_resp.status_code != 200:
                    continue

                ann_soup = BeautifulSoup(ann_resp.text, "html.parser")
                page_text = ann_soup.get_text(" ", strip=True)

                # Extract ex-date
                ex_match = re.search(r"Ex date.*?(\d{1,2} \w+ \d{4})", page_text)
                pay_match = re.search(r"Payment date.*?(\d{1,2} \w+ \d{4})", page_text)
                frank_match = re.search(r"Franked.*?(\d+\.?\d*)\s*%", page_text)

                ex_date = ex_match.group(1) if ex_match else None
                pay_date = pay_match.group(1) if pay_match else None
                franking = float(frank_match.group(1)) if frank_match else None

                if ex_date:
                    try:
                        ex_date_parsed = pd.to_datetime(ex_date, dayfirst=True)
                        if start_date <= ex_date_parsed <= end_date:
                            dividend_records.append({
                                "Ex-Date": ex_date_parsed.date(),
                                "Payment Date": pay_date,
                                "Franking %": franking
                            })
                    except:
                        continue

        return dividend_records

    except:
        return []


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

    asx_data = get_asx_dividend_data(ticker)

    for date, amount in dividends.items():
        ex_date = date.date()

        # Match ASX record by date
        match = next((d for d in asx_data if d["Ex-Date"] == ex_date), None)

        pay_date = match["Payment Date"] if match else None
        franking = match["Franking %"] if match else None

        all_data.append({
            "Ticker": ticker.replace(".AX", ""),
            "Ex-Date": ex_date,
            "Payment Date": pay_date,
            "Dividend per Share": round(amount, 6),
            "Franking %": franking
        })

    time.sleep(1)

df = pd.DataFrame(all_data)

if not df.empty:
    df = df.sort_values(by=["Ex-Date", "Ticker"])

filename = f"Dividend_Report_ASX_{end_date.strftime('%b_%Y')}.xlsx"
df.to_excel(filename, index=False)

print(f"File created: {filename}")
