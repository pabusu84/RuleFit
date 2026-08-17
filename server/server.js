// 백업 기초 데이터 (국내 종목 배당금 및 주가 추가)
const BACKUP_STOCKS = {
    // 국내 종목
    "005930.KS": { name: "삼성전자", price: 60000, divPerShare: 1444, months: [4,5,8,11], currency: "KRW" },
    "005935.KS": { name: "삼성전자우", price: 50000, divPerShare: 1445, months: [4,5,8,11], currency: "KRW" },
    "000660.KS": { name: "SK하이닉스", price: 180000, divPerShare: 1500, months: [4,5,8,11], currency: "KRW" },
    "006400.KS": { name: "삼성SDI", price: 350000, divPerShare: 1000, months: [4], currency: "KRW" },
    "005387.KS": { name: "현대차2우B", price: 150000, divPerShare: 11500, months: [4,5,8,11], currency: "KRW" },
    "034020.KS": { name: "두산에너빌리티", price: 20000, divPerShare: 0, months: [], currency: "KRW" },
    "472150.KS": { name: "TIGER 배당커버드콜액티브", price: 10000, divPerShare: 70, months: [1,2,3,4,5,6,7,8,9,10,11,12], currency: "KRW" },
    "486290.KS": { name: "TIGER 미국나스닥100타겟데일리커버드콜", price: 11080, divPerShare: 100, months: [1,2,3,4,5,6,7,8,9,10,11,12], currency: "KRW" },
    "0177N0.KS": { name: "KODEX 삼성전자SK하이닉스채권혼합50", price: 14145, divPerShare: 200, months: [1,4,7,10], currency: "KRW" },
    
    // 해외 종목
    "GPIX": { name: "GPIX", price: 54.96, divPerShare: 0.45, months: [1,2,3,4,5,6,7,8,9,10,11,12], currency: "USD" },
    "JEPQ": { name: "JEPQ", price: 57.09, divPerShare: 0.42, months: [1,2,3,4,5,6,7,8,9,10,11,12], currency: "USD" },
    "AAPL": { name: "AAPL", price: 220.0, divPerShare: 0.25, months: [2,5,8,11], currency: "USD" }
};
