import json
import urllib.request
import re
from bs4 import BeautifulSoup
import yfinance as yf

def get_exchange_rate():
    try:
        url = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
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
        # 네이버 차단 방지를 위한 브라우저 헤더 설정
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        # 1. 현재가 수집
        no_today = soup.select_one('.no_today .blind')
        if no_today:
            price = float(no_today.text.replace(',', ''))

        # 2. 배당금 수집 (cop_analysis 섹션)
        cop_analysis = soup.select_one('.section.cop_analysis')
        if cop_analysis:
            trs = cop_analysis.select('tbody tr')
            for tr in trs:
                title_td = tr.select_one('th')
                if title_td and '주당배당금' in title_td.text:
                    tds = tr.select('td')
                    for td in reversed(tds):
                        val_str = td.text.strip().replace(',', '')
                        if val_str and val_str != '-' and val_str != '':
                            try:
                                div_per_share = float(val_str)
                                break
                            except ValueError:
                                continue
                    break

        # 주요 분기/월 배당 종목 예외 처리
        if clean_code in ['005930', '005935', '000660']:
            months = [4, 5, 8, 11]
        elif clean_code in ['472150']:
            months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        print(f"[성공] 한국 주식 {clean_code} -> 현재가: {price}, 배당금: {div_per_share}")

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

        print(f"[성공] 미국 주식 {ticker_symbol} -> 현재가: {price}")
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
        print(f"targets.json 읽기 오류: {e}")
        targets = []

    exchange_rate = get_exchange_rate()
    result_data = {
        "exchangeRate": exchange_rate,
        "stocks": {}
    }

    for t in targets:
        t_clean = t.strip().upper()
        
        # 한국 주식 처리 (숫자 6자리, .KS, .KQ 지원)
        is_kr = t_clean.endswith('.KS') or t_clean.endswith('.KQ') or (len(t_clean) == 6 and t_clean.isdigit())
        
        if is_kr:
            data = get_kr_stock_data(t_clean)
            raw_code = t_clean.replace('.KS', '').replace('.KQ', '').zfill(6)
            
            # index.html이 어떤 형식으로 호출하든 모두 응답할 수 있도록 다중 키 저장
            result_data["stocks"][raw_code] = data
            result_data["stocks"][f"{raw_code}.KS"] = data
            result_data["stocks"][t_clean] = data
        else:
            data = get_us_stock_data(t_clean)
            result_data["stocks"][t_clean] = data

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print("data.json 저장 완료!")

if __name__ == '__main__':
    main()
