
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import yfinance as yf
import requests
from datetime import datetime

import os
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_USER_ID = "saynull"
SHEET_NAME = "YieldMax_고배당_모니터링"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_USER_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1

    data = sheet.get_all_records()
    updated_data = []

    for idx, row in enumerate(data, start=2):
        ticker = row['티커']
        info = yf.Ticker(ticker)

        try:
            price = info.info.get("regularMarketPrice", 0)
            dividends = info.dividends
            recent_dividend = dividends[-1] if len(dividends) > 0 else 0
            frequency = 12
            annual_dividend = round(recent_dividend * frequency, 2)
            yield_percent = round((annual_dividend / price) * 100, 2) if price else 0
        except Exception:
            price, annual_dividend, yield_percent = 0, 0, 0

        sheet.update(f"C{idx}", price)
        sheet.update(f"D{idx}", annual_dividend)
        sheet.update(f"E{idx}", yield_percent)
        sheet.update(f"F{idx}", datetime.today().strftime("%Y-%m-%d"))
        updated_data.append((ticker, row['ETF 이름'], yield_percent))

    top_etfs = sorted(updated_data, key=lambda x: x[2], reverse=True)[:5]
    msg = "*Top 5 YieldMax ETF 배당수익률 (6시간 주기 업데이트)*\n"
    for t in top_etfs:
        msg += f"- {t[0]} ({t[1]}): {t[2]}%\n"

    send_telegram_message(msg)

if __name__ == "__main__":
    main()
