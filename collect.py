import yfinance as yf
import json
import datetime

TICKERS = {
    # 미국 주식 및 ETF
    "JEPQ": "JEPQ",
    "SCHD": "SCHD",
    "O": "O",
    "GPIX": "GPIX",

    # 한국 주식 & ETF
    "SK하이닉스": "000660.KS",
    "현대차2우B": "005387.KS",
    "삼성전자": "005930.KS",
    "삼성전자우": "005935.KS",
    "삼성SDI": "006400.KS",
    "두산에너빌리티": "034020.KS",
    "TIME 미국나스닥100액티브": "426030.KS",
    "TIGER 배당커버드콜액티브": "472150.KS"
}

# 월배당 종목 리스트 (1~12월 지정 및 최근 배당금x12 적용)
MONTHLY_DIVIDEND_STOCKS = ["JEPQ", "O", "GPIX", "TIGER 배당커버드콜액티브", "472150.KS"]

def get_exchange_rate():
    try:
        ticker = yf.Ticker("KRW=X")
        data = ticker.history(period="1d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
    except Exception as e:
        print(f"환율 수집 실패: {e}")
    return 1350.0

def collect_data():
    exchange_rate = get_exchange_rate()
    result = {
        "exchangeRate": exchange_rate,
        "updatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stocks": {}
    }

    for name, ticker_symbol in TICKERS.items():
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            # 현재가 가져오기
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0
            
            # 배당금 및 배당월 계산
            dividends = stock.dividends
            div_per_share = 0
            months = []

            if name in MONTHLY_DIVIDEND_STOCKS or ticker_symbol in MONTHLY_DIVIDEND_STOCKS:
                # 월배당 종목 처리: 1~12월 모두 지정
                months = list(range(1, 13))
                if not dividends.empty:
                    # 가장 최근 1회 배당금 * 12회 = 연간 배당금 추정
                    last_div = dividends.iloc[-1]
                    div_per_share = round(last_div * 12, 4)
                else:
                    div_per_share = info.get("dividendRate", 0)
            else:
                # 일반 주식 (분기/반기 배당)
                if not dividends.empty:
                    # 최근 1년(365일) 내 배당금 합산
                    one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
                    recent_divs = dividends[dividends.index >= one_year_ago.strftime('%Y-%m-%d')]
                    
                    if not recent_divs.empty:
                        div_per_share = round(recent_divs.sum(), 4)
                        months = sorted(list(set([d.month for d in recent_divs.index])))
                    else:
                        div_per_share = info.get("dividendRate", 0)
                else:
                    div_per_share = info.get("dividendRate", 0)

            # 통화 구분
            currency = "KRW" if ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ") else "USD"

            result["stocks"][name] = {
                "ticker": ticker_symbol,
                "price": round(price, 2),
                "divPerShare": round(div_per_share, 4),
                "months": months,
                "currency": currency
            }
            print(f" 성공: {name} ({ticker_symbol}) - 현재가: {price}, 연배당금: {div_per_share}")

        except Exception as e:
            print(f" 실패: {name} ({ticker_symbol}) - {e}")

    # data.json 저장
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    collect_data()
