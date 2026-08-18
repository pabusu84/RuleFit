import json
import urllib.request
from bs4 import BeautifulSoup
import yfinance as yf

def get_exchange_rate():
    # 방법 1: yfinance를 통한 환율 수집 (가장 안정적)
    try:
        ticker = yf.Ticker("USDKRW=X")
        rate = ticker.fast_info.last_price
        if rate and rate > 100:
            print(f"yfinance 환율 수집 성공: {rate}")
            return round(float(rate), 2)
    except Exception as e:
        print(f"yfinance 환율 수집 실패: {e}")

    # 방법 2: 네이버 환율 페이지 (fallback)
    try:
        url = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=5).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')
        el = soup.select_one('p.no_today')
        if el:
            # 줄바꿈, 탭, 공백 전부 제거 후 숫자와 소수점만 추출
            raw = el.text.strip().replace(',', '').replace('\n', '').replace('\r', '').replace('\t', '')
            import re
            num_match = re.search(r'[\d]+\.?[\d]*', raw)
            if num_match:
                rate = float(num_match.group())
                print(f"네이버 환율 수집 성공: {rate}")
                return rate
    except Exception as e:
        print(f"네이버 환율 수집 실패: {e}")

    print("환율 수집 전부 실패, 기본값 1350.0 사용")
    return 1350.0

def get_kr_stock_data(code):
    clean_code = code.replace('.KS', '').replace('.KQ', '').zfill(6)
    yf_code = f"{clean_code}.KS"

    price = 0.0
    div_per_share = 0.0
    months = [4]

    # 방법 1: yfinance로 현재가 수집 (안정적)
    try:
        ticker = yf.Ticker(yf_code)
        info = ticker.fast_info
        last_price = info.last_price
        if last_price and last_price > 0:
            price = round(float(last_price), 0)
            print(f"  yfinance 가격 [{clean_code}]: {price:,.0f}원")
    except Exception as e:
        print(f"  yfinance 주가 수집 오류 [{clean_code}]: {e}")

    # 방법 2: 네이버로 배당금 수집 (yfinance에 한국주식 배당정보 부실함)
    try:
        url = f"https://finance.naver.com/item/main.naver?code={clean_code}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=7).read().decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        # 네이버에서 가격을 못 가져왔을 경우에만 네이버 가격 시도
        if price == 0.0:
            no_today = soup.select_one('.no_today .blind')
            if no_today:
                try:
                    naver_price = float(no_today.text.strip().replace(',', ''))
                    # 합리적인 가격 범위인지 검증 (100원~100만원 사이)
                    if 100 <= naver_price <= 10000000:
                        price = naver_price
                        print(f"  네이버 가격 [{clean_code}]: {price:,.0f}원")
                except ValueError:
                    pass

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
        print(f"  네이버 크롤링 오류 [{clean_code}]: {e}")

    # 배당금 기본값 (네이버에서 수집 실패 시)
    default_divs = {
        '005930': (1444.0, [5, 8, 11, 4]),      # 삼성전자
        '005935': (1445.0, [5, 8, 11, 4]),      # 삼성전자우
        '000660': (1200.0, [5, 8, 11, 4]),      # SK하이닉스
        '006400': (1000.0, [4]),                # 삼성SDI
        '005387': (11500.0, [4, 5, 8, 11]),     # 현대차2우B
        '034020': (0.0, [4]),                   # 두산에너빌리티
        '472150': (1040.0, list(range(1, 13))), # TIGER 배당커버드콜
        '486290': (1200.0, list(range(1, 13))), # TIGER 나스닥100 커버드콜
        '453850': (120.0, list(range(1, 13))),  # TIME 미국나스닥100액티브
        '0177n0': (350.0, [4, 5, 8, 11]),       # KODEX 삼성전자SK하이닉스채권혼합50
    }

    if clean_code.lower() in default_divs:
        def_div, def_months = default_divs[clean_code.lower()]
        if div_per_share == 0:
            div_per_share = def_div
        months = def_months
    elif clean_code in default_divs:
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
    import os
    targets = set()
    
    # 1. holdings.json에서 코드 추출 시도
    try:
        if os.path.exists('holdings.json'):
            with open('holdings.json', 'r', encoding='utf-8') as f:
                holdings = json.load(f)
                for item in holdings:
                    code = item.get('code')
                    if code:
                        targets.add(code.strip().upper())
            print(f"holdings.json에서 {len(targets)}개의 종목을 탐지하여 수집 대상으로 설정했습니다.")
    except Exception as e:
        print(f"holdings.json 분석 오류: {e}")

    # 2. holdings.json에 종목이 없으면 targets.json 백업 활용
    if not targets:
        try:
            if os.path.exists('targets.json'):
                with open('targets.json', 'r', encoding='utf-8') as f:
                    targets_list = json.load(f)
                    for t in targets_list:
                        if t:
                            targets.add(t.strip().upper())
            print(f"targets.json에서 {len(targets)}개의 수집 대상을 로드했습니다.")
        except Exception:
            pass

    # 3. 둘 다 비어있을 경우 기본 백업 코드 적용
    if not targets:
        targets = {"005930.KS", "005935.KS", "000660.KS", "006400.KS", "005387.KS", "034020.KS", "472150.KS", "486290.KS", "GPIX", "JEPQ", "AAPL"}
        print(f"기본 백업 종목 {len(targets)}개에 대해 수집을 진행합니다.")

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
