import yfinance as yf
import json
import datetime

# 수집 대상 종목 리스트
TICKERS = {
    # 미국 주식 및 ETF
    "JEPI": "JEPI",
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

# 월배당 종목 지정 (1~12월 지급 및 최근 배당금 x 12 적용)
MONTHLY_DIVIDEND_STOCKS = ["JEPI", "JEPQ", "O", "GPIX", "TIGER 배당커버드콜액티브", "472150.KS"]

def get_exchange_rate():
    try:
        ticker = yf.Ticker("KRW=X")
        data = ticker.history(period="1d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
    except Exception as e:
        print(f"환율 수집 오류: {e}")
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
            
            # 1. 현재가 수집 (여러 경로 시도)
            fast_info = getattr(stock, 'fast_info', {})
            price = fast_info.get('last_price') or stock.info.get('currentPrice') or stock.info.get('regularMarketPrice') or stock.info.get('previousClose') or 0
            
            # 2. 배당금 수집
            div_per_share = 0
            months = []
            
            # yfinance info에서 연간 배당률 가져오기 시도
            info_div_rate = stock.info.get("dividendRate", 0) or 0

            if name in MONTHLY_DIVIDEND_STOCKS or ticker_symbol in MONTHLY_DIVIDEND_STOCKS:
                months = list(range(1, 13))
                try:
                    dividends = stock.dividends
                    if not dividends.empty:
                        last_div = dividends.iloc[-1]
                        div_per_share = round(last_div * 12, 4)
                    else:
                        div_per_share = info_div_rate
                except:
                    div_per_share = info_div_rate
            else:
                try:
                    dividends = stock.dividends
                    if not dividends.empty:
                        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
                        recent_divs = dividends[dividends.index >= one_year_ago.strftime('%Y-%m-%d')]
                        if not recent_divs.empty:
                            div_per_share = round(recent_divs.sum(), 4)
                            months = sorted(list(set([d.month for d in recent_divs.index])))
                        else:
                            div_per_share = info_div_rate
                    else:
                        div_per_share = info_div_rate
                except:
                    div_per_share = info_div_rate

            currency = "KRW" if ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ") else "USD"

            # 종목명/티커 두 가지 키로 모두 저장 (대소문자/검색 호환성 극대화)
            stock_data = {
                "ticker": ticker_symbol,
                "price": round(price, 2),
                "divPerShare": round(div_per_share, 4),
                "months": months,
                "currency": currency
            }
            
            result["stocks"][name] = stock_data
            result["stocks"][ticker_symbol] = stock_data
            result["stocks"][name.lower()] = stock_data
            result["stocks"][name.upper()] = stock_data

            print(f"성공: {name} ({ticker_symbol}) - 현재가: {price}, 연배당금: {div_per_share}")

        except Exception as e:
            print(f"실패: {name} ({ticker_symbol}) - {e}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    collect_data()
