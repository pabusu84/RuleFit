import json
import urllib.request
from bs4 import BeautifulSoup
import yfinance as yf

def get_exchange_rate():
    try:
        url = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=5).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')
        rate_text = soup.select_one('p.no_today').text.strip()
        return float(rate_text.replace(',', ''))
    except Exception as e:
        print(f"환율 수집 실패: {e}")
        return 1350.0

def get_kr_stock_data(code):
    clean_code = code.replace('.KS', '').replace('.KQ', '').zfill(6)
    url = f"https://finance.naver.com/item/main.naver?code={clean_code}"
    
    price = 0.0
    div_per_share = 0.0
    months = [4]

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=5).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        # 현재가 수집
        no_today = soup.select_one('.no_today .blind')
        if no_today:
            price = float(no_today.text.replace(',', ''))

        # 배당금 탐색
        for tr in soup.select('table tr'):
            if '주당배당금' in tr.text:
                tds = tr.select('td')
                for td in reversed(tds):
                    val = td.text.strip().replace(',', '')
                    if val and val != '-' and val != 'N/A':
                        try:
                            div_per_share = float(val)
                            break
                        except ValueError:
                            continue
                if div_per_share > 0:
                    break
    except Exception as e:
        print(f"네이버 크롤링 오류 [{clean_code}]: {e}")

    # 네이버에서 배당금을 못 가져올 경우를 대비한 든든한 방어 로직 (주요 종목 기본값)
    default_divs = {
        '005930': (1444.0, [5, 8, 11, 4]),     # 삼성전자
        '005935': (1445.0, [5, 8, 11, 4]),     # 삼성전자우
        '000660': (1200.0, [5, 8, 11, 4]),     # SK하이닉스
        '006400': (1000.0, [4]),               # 삼성SDI
        '005387': (11500.0, [4]),              # 현대차2우B
        '034020': (0.0, [4]),                  # 두산에너빌리티
        '472150': (1040.0, list(range(1, 13))) # TIGER 배당커버드콜
    }

    if clean_code in default_divs:
        def_div, def_months = default_divs[clean_code]
        if div_per_share == 0:
            div_per_share = def_div
        months = def_months

    return {
        "price": price,
        "divPerShare": div_per_share,
        "months": months,
        "currency": "KRW"
    }

def get_us_stock_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.fast_info
        price = info.last_price or 0.0

        hist_div = ticker.dividends
        div_per_share = 0.0
        months = []

        if not hist_div.empty:
            recent_1y = hist_div.tail(12)
            div_per_share = float(recent_1y.sum())
            months = sorted(list(set(recent_1y.index.month)))

        return {
            "price": round(price, 2),
            "divPerShare": round(div_per_share, 4),
            "months": months,
            "currency": "USD"
        }
    except Exception as e:
        print(f"야후 파이낸스 오류 [{ticker_symbol}]: {e}")
        return {"price": 0.0, "divPerShare": 0.0, "months": [], "currency": "USD"}

def main():
    try:
        with open('targets.json', 'r', encoding='utf-8') as f:
            targets = json.load(f)
    except Exception:
        targets = []

    exchange_rate = get_exchange_rate()
    result_data = {"exchangeRate": exchange_rate, "stocks": {}}

    for t in targets:
        t_clean = t.strip().upper()
        is_kr = t_clean.endswith('.KS') or t_clean.endswith('.KQ') or (len(t_clean) == 6 and t_clean.isdigit())
        
        if is_kr:
            data = get_kr_stock_data(t_clean)
            raw_code = t_clean.replace('.KS', '').replace('.KQ', '').zfill(6)
            result_data["stocks"][raw_code] = data
            result_data["stocks"][f"{raw_code}.KS"] = data
        else:
            data = get_us_stock_data(t_clean)
            result_data["stocks"][t_clean] = data

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print("수집 및 data.json 업데이트 완료!")

if __name__ == '__main__':
    main()
