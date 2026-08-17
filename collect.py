import json
import urllib.request
import re
from bs4 import BeautifulSoup
import yfinance as yf

def get_exchange_rate():
    try:
        url = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')
        rate_text = soup.select_one('p.no_today').text.strip()
        return float(rate_text.replace(',', ''))
    except Exception as e:
        print(f"환율 수집 실패: {e}")
        return 1350.0

def get_kr_stock_data(code):
    clean_code = code.replace('.KS', '').replace('.KQ', '')
    url = f"https://finance.naver.com/item/main.naver?code={clean_code}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        no_today = soup.select_one('.no_today .blind')
        price = float(no_today.text.replace(',', '')) if no_today else 0.0

        div_per_share = 0.0
        cop_analysis = soup.select_one('.section.cop_analysis')
        if cop_analysis:
            trs = cop_analysis.select('tbody tr')
            for tr in trs:
                title_td = tr.select_one('th')
                if title_td and '주당배당금' in title_td.text:
                    tds = tr.select('td')
                    for td in reversed(tds):
                        val_str = td.text.strip().replace(',', '')
                        if val_str and val_str != '-':
                            try:
                                div_per_share = float(val_str)
                                break
                            except ValueError:
                                continue
                    break

        # 배당월 설정
        if clean_code in ['005930', '005935', '000660']:
            months = [5, 8, 11, 4]
        elif clean_code in ['472150']:
            months = [1,2,3,4,5,6,7,8,9,10,11,12]
        else:
            months = [4]

        return {
            "price": price,
            "divPerShare": div_per_share,
            "months": months,
            "currency": "KRW"
        }
    except Exception as e:
        print(f"네이버 수집 실패 [{clean_code}]: {e}")
        return {"price": 0.0, "divPerShare": 0.0, "months": [], "currency": "KRW"}

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
        print(f"Yahoo 수집 실패 [{ticker_symbol}]: {e}")
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
        if t_clean.endswith('.KS') or t_clean.endswith('.KQ') or (len(t_clean) == 6 and t_clean.isdigit()):
            data = get_kr_stock_data(t_clean)
            # 호환성을 위해 .KS 붙은 이름과 안 붙은 이름 둘 다 저장
            raw_code = t_clean.replace('.KS', '').replace('.KQ', '')
            result_data["stocks"][raw_code] = data
            result_data["stocks"][f"{raw_code}.KS"] = data
        else:
            data = get_us_stock_data(t_clean)
            result_data["stocks"][t_clean] = data

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print("data.json 저장 완료!")

if __name__ == '__main__':
    main()
