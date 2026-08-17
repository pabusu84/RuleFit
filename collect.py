import json
import os
import requests
import yfinance as yf

TARGETS_FILE = "targets.json"
OUTPUT_FILE = "data.json"

def load_targets():
    if os.path.exists(TARGETS_FILE):
        with open(TARGETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 기본값
    return ["JEPI", "GPIX", "JEPQ", "005930.KS"]

def fetch_exchange_rate():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/USDKRW=X"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10).json()
        return res['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception as e:
        print(f"환율 수집 실패 (기본값 사용): {e}")
        return 1350.0

def collect_data():
    targets = load_targets()
    exchange_rate = fetch_exchange_rate()
    stocks_data = {}

    for symbol in targets:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 주가
            price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            
            # 주당 연간 배당금
            div_rate = info.get('dividendRate') or 0
            
            # 배당 지급월 추출 (최근 배당 내역 기반)
            dividends = ticker.dividends
            months = []
            if not dividends.empty:
                recent_divs = dividends.tail(12)
                months = sorted(list(set(recent_divs.index.month)))

            currency = info.get('currency', 'USD')

            stocks_data[symbol] = {
                "ticker": symbol,
                "price": price,
                "divPerShare": div_rate,
                "months": months,
                "currency": currency
            }
            print(f"수집 성공: {symbol}")
        except Exception as e:
            print(f"수집 실패 ({symbol}): {e}")

    result = {
        "exchangeRate": exchange_rate,
        "stocks": stocks_data
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    collect_data()
