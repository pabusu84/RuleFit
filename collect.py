def collect_data():
    targets = load_targets()
    exchange_rate = fetch_exchange_rate()
    stocks_data = {}

    for symbol in targets:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 주가 수집
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0
            
            # 연간 배당금 수집 (기존 방식 보완)
            div_rate = info.get('dividendRate')
            if div_rate is None:
                div_rate = info.get('trailingAnnualDividendRate') or 0

            # 배당 지급월 추출
            dividends = ticker.dividends
            months = []
            if not dividends.empty:
                recent_divs = dividends.tail(12)
                months = sorted(list(set(recent_divs.index.month)))

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
