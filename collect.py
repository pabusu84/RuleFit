import json
import yfinance as yf

# 관리할 주요 종목 매핑 (입력 가능한 대소문자/한글 처리)
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
    result = {}
    for key_name, ticker in TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            price = info.last_price if info.last_price else 0
            
            divs = stock.dividends
            annual_div = 0
            months = []
            
            if not divs.empty:
                recent_1yr = divs.last('1y')
                annual_div = float(recent_1yr.sum())
                months = sorted(list(set(recent_1yr.index.month)))

            data_item = {
                "ticker": ticker,
                "price": round(price, 2),
                "divPerShare": round(annual_div, 2),
                "months": months
            }
            
            # 대문자, 소문자, 키값 모두 저장하여 매칭률 상향
            result[key_name.upper()] = data_item
            result[key_name.lower()] = data_item
            result[key_name] = data_item

        except Exception as e:
            print(f"Error fetching {key_name}: {e}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    get_stock_data()
