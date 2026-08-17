import json
import urllib.request
import re
from bs4 import BeautifulSoup
import yfinance as yf

def get_exchange_rate():
    try:
        url = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req).read().decode('euc-kr', errors='replace')
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        # 1. 현재가 수집
        no_today = soup.select_one('.no_today .blind')
        if no_today:
            price = float(no_today.text.replace(',', ''))

        # 2. 배당금/분배금 수집
        # 일반 주식 재무제표 표 탐색
        for tr in soup.select('table tr'):
            text = tr.text
            if '주당배당금' in text or '주당 배당금' in text:
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

        # 분기배당 및 월배당 ETF 기본 배당금/분배금 예외 보완
        if clean_code in ['005930', '005935']: # 삼성전자, 삼성전자우
            if div_per_share == 0: div_per_share = 1444.0
            months = [5, 8, 11, 4]
        elif clean_code == '000660': # SK하이닉스
            if div_per_share == 0: div_per_share = 1200.0
            months = [5, 8, 11, 4]
        elif clean_code == '472150': # TIGER 배당커버드콜액티브
            if div_per_share == 0: div_per_share = 1040.0 # 연간 추정 분배금
            months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    except Exception as e:
        print(f"[실패] 네이버 수집 오류 ({clean_code}): {e}")

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
        price = info.last_price

        hist_div = ticker.dividends
        div_per_share = 0.0
        months = []

        if not hist_div.empty:
            recent_1y = hist_div.tail(12)
            div_per_share = float(recent_1y.sum())
            months = sorted(list(set(recent_1y.index.month)))

        return {
            "price": round(price, 2) if price else 0.0,
            "divPerShare": round(div_per_share, 4),
            "months": months,
            "currency": "USD"
        }
    except Exception as e:
        print(f"[실패] 야후 수집 오류 ({ticker_symbol}): {e}")
        return {"price": 0.0, "divPerShare": 0.0, "months": [], "currency": "USD"}

def main():
    try:
        with open('targets.json', 'r', encoding='utf-8') as f:
            targets = json.load(f)
    except Exception as e:
        targets = []

    exchange_rate = get_exchange_rate()
    result_data = {
        "exchangeRate": exchange_rate,
        "stocks": {}
    }

    for t in targets:
        t_clean = t.strip().upper()
        is_kr = t_clean.endswith('.KS') or t_clean.endswith('.KQ') or (len(t_clean) == 6 and t_clean.isdigit())
        
        if is_kr:
            data = get_kr_stock_data(t_clean)
            raw_code = t_clean.replace('.KS', '').replace('.KQ', '').zfill(6)
            result_data["stocks"][raw_code] = data
            result_data["stocks"][f"{raw_code}.KS"] = data
            result_data["stocks"][t_clean] = data
        else:
            data = get_us_stock_data(t_clean)
            result_data["stocks"][t_clean] = data

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
