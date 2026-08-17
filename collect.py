import json
import yfinance as yf

# 관리할 주요 종목 리스트 (필요시 추가 가능)
TICKERS = {
    "SCHD": "SCHD",
    "JEPQ": "JEPQ",
    "O": "O",
    "삼성전자": "005930.KS",
    "맥쿼리인프라": "088980.KS",
    "SOL미국배당다우존스": "446720.KS",
    "TIGER미국배당다우존스": "458730.KS"
}

def get_stock_data():
    result = {}
    for name, ticker in TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            price = info.last_price
            
            # 배당 내역 추출
            divs = stock.dividends
            annual_div = 0
            months = []
            
            if not divs.empty:
                # 최근 1년 배당금 합계
                recent_1yr = divs.last('1y')
                annual_div = float(recent_1yr.sum())
                # 배당 지급월 추출
                months = sorted(list(set(recent_1yr.index.month)))

            result[name] = {
                "ticker": ticker,
                "price": round(price, 2),
                "divPerShare": round(annual_div, 2),
                "months": months
            }
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    get_stock_data()
