import json
import yfinance as yf
from curl_cffi import requests

TICKERS = {
    "JEPQ": "JEPQ",
    "SCHD": "SCHD",
    "O": "O",
    "삼성전자": "005930.KS",
    "맥쿼리인프라": "088980.KS",
    "SOL미국배당다우존스": "446720.KS",
    "TIGER미국배당다우존스": "458730.KS"
}

def get_stock_data():
    result = {"stocks": {}, "exchangeRate": 1350}
    session = requests.Session(impersonate="chrome")

    # 1. 환율 수집
    try:
        ex = yf.Ticker("KRW=X", session=session)
        rate = ex.fast_info.last_price
        if rate:
            result["exchangeRate"] = round(rate, 2)
    except Exception as e:
        print(f"Exchange rate error: {e}")

    # 2. 종목 데이터 수집
    for key_name, ticker in TICKERS.items():
        try:
            stock = yf.Ticker(ticker, session=session)
            fast = stock.fast_info
            
            price = fast.last_price or 0
            
            # 배당금 수집 (기본값 세팅으로 실패 방지)
            annual_div = 0
            try:
                info = stock.info
                annual_div = info.get("dividendRate") or info.get("trailingAnnualDividendRate") or 0
            except:
                pass

            months = []
            try:
                divs = stock.dividends
                if not divs.empty:
                    months = sorted(list(set(divs.last('1y').index.month)))
            except:
                pass

            currency = "KRW" if ticker.endswith(".KS") else "USD"

            data_item = {
                "ticker": ticker,
                "price": round(price, 2),
                "divPerShare": round(annual_div, 2),
                "months": months,
                "currency": currency
            }

            result["stocks"][key_name.upper()] = data_item
            result["stocks"][key_name.lower()] = data_item
            result["stocks"][key_name] = data_item

        except Exception as e:
            print(f"Error fetching {key_name}: {e}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    get_stock_data()
