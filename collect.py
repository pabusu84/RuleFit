import json
import os
import requests
import yfinance as yf

TARGETS_FILE = "targets.json"
OUTPUT_FILE = "data.json"

def load_targets():
    if os.path.exists(TARGETS_FILE):
        try:
            with open(TARGETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"targets.json 로드 실패: {e}")
    return ["GPIX", "JEPQ", "AAPL", "005930.KS"]

def fetch_exchange_rate():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/USDKRW=X"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10).json()
        return res['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception as e:
        print(f"환율 수집 실패 (기본값 1350 사용): {e}")
        return 1350.0

def collect_data():
    targets = load_targets()
    exchange_rate = fetch_exchange_rate()
    stocks_data = {}

    for symbol in targets:
        try:
            ticker = yf.Ticker(symbol)
            
            # info 조회 중 에러 발생 시 예외 처리
            try:
                info = ticker.info or {}
            except Exception:
                info = {}

            # 주가 수집
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0

            # 연간 주당 배당금 수집
            div_rate = info.get('dividendRate')
            if div_rate is None:
                div_rate = info.get('trailingAnnualDividendRate') or 0

            # 배당 지급월 추출
            months = []
            try:
                dividends = ticker.dividends
                if dividends is not None and not dividends.empty:
                    recent_divs = dividends.tail(12)
                    months = sorted(list(set(recent_divs.index.month)))
            except Exception as e:
                print(f"{symbol} 배당 월 수집 스킵: {e}")

            currency = info.get('currency', 'USD')

            stocks_data[symbol] = {
                "ticker": symbol,
                "price": price,
                "divPerShare": float(div_rate),
                "months": months,
                "currency": currency
            }
            print(f"수집 성공: {symbol} - 주가: {price}, 배당금: {div_rate}")
        except Exception as e:
            print(f"수집 실패 ({symbol}): {e}")

    result = {
        "exchangeRate": exchange_rate,
        "stocks": stocks_data
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("data.json 저장 완료")

if __name__ == "__main__":
    collect_data()
