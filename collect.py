import json
import yfinance as yf

# 관리할 종목 리스트 (한국 주식은 .KS 붙임)
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
    
    # 1. 환율 수집
    try:
        ex_ticker = yf.Ticker("KRW=X")
        rate = ex_ticker.fast_info.last_price or ex_ticker.info.get("regularMarketPrice")
        if rate:
            result["exchangeRate"] = round(rate, 2)
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")

    # 2. 종목 데이터 수집
    for key_name, ticker in TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            fast_info = stock.fast_info

            # 주가 가져오기
            price = fast_info.last_price or info.get("regularMarketPrice") or info.get("previousClose") or 0
            
            # 연간 주당 배당금 가져오기 (info 우선 활용)
            annual_div = info.get("dividendRate") or info.get("trailingAnnualDividendRate") or 0
            
            # info에 배당금이 없을 경우 과거 배당 내역 1년치 합산 fallback
            if not annual_div:
                try:
                    divs = stock.dividends
                    if not divs.empty:
                        annual_div = float(divs.last('1y').sum())
                except:
                    annual_div = 0

            # 지급월 추출 (기본 월 설정 또는 history에서 추출)
            months = []
            try:
                divs = stock.dividends
                if not divs.empty:
                    months = sorted(list(set(divs.last('1y').index.month)))
            except:
                months = []

            currency = "KRW" if ticker.endswith(".KS") else "USD"

            data_item = {
                "ticker": ticker,
                "price": round(price, 2),
                "divPerShare": round(annual_div, 2),
                "months": months,
                "currency": currency
            }
            
            # 다양한 검색어 호환성 확보
            result["stocks"][key_name.upper()] = data_item
            result["stocks"][key_name.lower()] = data_item
            result["stocks"][key_name] = data_item

        except Exception as e:
            print(f"Error fetching {key_name}: {e}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    get_stock_data()
