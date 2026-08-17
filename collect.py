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
        rate = float(rate_text.replace(',', ''))
        return rate
    except Exception as e:
        print(f"환율 수집 실패 (기본값 1350원 사용): {e}")
        return 1350.0

def get_kr_stock_data(code):
    """네이버 증권에서 국내 주식 현재가, 주당 배당금, 배당월 수집"""
    code = code.replace('.KS', '').replace('.KQ', '')
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        # 1. 현재가 수집
        no_today = soup.select_one('.no_today .blind')
        price = float(no_today.text.replace(',', '')) if no_today else 0.0

        # 2. 기업개요/재무제표 표에서 주당배당금(원) 추출
        div_per_share = 0.0
        months = []

        cop_analysis = soup.select_one('.section.cop_analysis')
        if cop_analysis:
            th_list = cop_analysis.select('thead tr:nth-of-type(2) th')
            # 최근 결산/예상 연월 추출 (예: 2023.12, 2024.12 등)
            recent_months = []
            for th in th_list:
                txt = th.text.strip()
                m = re.search(r'\d{4}\.(\d{2})', txt)
                if m:
                    recent_months.append(int(m.group(1)))

            # 주당배당금(원) 행 찾기
            trs = cop_analysis.select('tbody tr')
            for tr in trs:
                title_td = tr.select_one('th')
                if title_td and '주당배당금' in title_td.text:
                    tds = tr.select('td')
                    # 가장 최근 확정/예상 배당금 수치 가져오기
                    for td in reversed(tds):
                        val_str = td.text.strip().replace(',', '')
                        if val_str and val_str != '-':
                            try:
                                div_per_share = float(val_str)
                                break
                            except ValueError:
                                continue
                    break

        # 기본 배당월 추정 (분기배당/결산배당)
        # 분기배당/월배당 특수 종목 처리
        if code in ['005930', '005935', '000660']: # 삼성전자, SK하이닉스 등
            months = [4, 5, 8, 11]
        elif code in ['472150']: # TIGER 배당커버드콜액티브 등 월배당 ETF
            months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        else:
            months = [4] # 일반 국내 주식 결산배당(4월 지급)

        return {
            "price": price,
            "divPerShare": div_per_share,
            "months": months,
            "currency": "KRW"
        }
    except Exception as e:
        print(f"네이버 수집 실패 [{code}]: {e}")
        return {"price": 0.0, "divPerShare": 0.0, "months": [], "currency": "KRW"}

def get_us_stock_data(ticker_symbol):
    """Yahoo Finance에서 미국 주식 데이터 수집"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.fast_info
        price = info.last_price

        # 배당금 및 지급월 수집
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
        print("targets.json 읽기 실패:", e)
        targets = []

    exchange_rate = get_exchange_rate()
    result_data = {
        "exchangeRate": exchange_rate,
        "stocks": {}
    }

    for t in targets:
        t_clean = t.strip().upper()
        print(f"[{t_clean}] 데이터 수집 중...")
        
        # 한국 주식 처리 (.KS, .KQ 또는 6자리 숫자)
        if t_clean.endswith('.KS') or t_clean.endswith('.KQ') or (len(t_clean) == 6 and t_clean.isdigit()):
            data = get_kr_stock_data(t_clean)
        else:
            data = get_us_stock_data(t_clean)

        result_data["stocks"][t_clean] = data

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print("data.json 저장 완료!")

if __name__ == '__main__':
    main()
