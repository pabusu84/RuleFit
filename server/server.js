const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

const HOLDINGS_FILE = path.join(__dirname, '../holdings.json');
const DATA_FILE = path.join(__dirname, '../data.json');

// 주식 및 배당 기초 데이터 백업 (data.json에 없는 경우 대비)
const BACKUP_STOCKS = {
    "005930.KS": { name: "삼성전자", price: 60000, divPerShare: 1444, officialYield: "2.4%", targetYield: "2.4%" },
    "005935.KS": { name: "삼성전자우", price: 50000, divPerShare: 1445, officialYield: "2.9%", targetYield: "2.9%" },
    "000660.KS": { name: "SK하이닉스", price: 180000, divPerShare: 1500, officialYield: "0.8%", targetYield: "0.8%" },
    "006400.KS": { name: "삼성SDI", price: 350000, divPerShare: 1000, officialYield: "0.3%", targetYield: "0.3%" },
    "005387.KS": { name: "현대차2우B", price: 150000, divPerShare: 11500, officialYield: "7.6%", targetYield: "7.6%" },
    "034020.KS": { name: "두산에너빌리티", price: 20000, divPerShare: 0, officialYield: "0.0%", targetYield: "0.0%" },
    "472150.KS": { name: "TIGER 배당커버드콜액티브", price: 10000, divPerShare: 840, officialYield: "4.2%", targetYield: "8.4%" },
    "486290.KS": { name: "TIGER 미국나스닥100타겟데일리커버드콜", price: 11080, divPerShare: 1200, officialYield: "2.1%", targetYield: "10.8%" },
    "0177N0.KS": { name: "KODEX 삼성전자SK하이닉스채권혼합50", price: 14145, divPerShare: 350, officialYield: "2.5%", targetYield: "2.5%" },
    "453850.KS": { name: "TIME 미국나스닥100액티브", price: 13000, divPerShare: 120, officialYield: "1.0%", targetYield: "1.0%" },
    "GPIX": { name: "GPIX", price: 54.96, divPerShare: 5.4, officialYield: "9.8%", targetYield: "9.8%", currency: "USD" },
    "JEPQ": { name: "JEPQ", price: 57.09, divPerShare: 5.04, officialYield: "8.8%", targetYield: "8.8%", currency: "USD" },
    "AAPL": { name: "AAPL", price: 220.0, divPerShare: 1.0, officialYield: "0.5%", targetYield: "0.5%", currency: "USD" }
};

// 기본 보유 종목 초기 데이터
const DEFAULT_HOLDINGS = [
    { name: "삼성전자우", code: "005935.KS", qty: 400, avg: 188396, account: "일반" },
    { name: "SK하이닉스", code: "000660.KS", qty: 30, avg: 2162833, account: "일반" },
    { name: "JEPQ", code: "JEPQ", qty: 373, avg: 57.09, account: "일반" },
    { name: "GPIX", code: "GPIX", qty: 287, avg: 54.96, account: "일반" },
    { name: "TIGER 배당커버드콜액티브", code: "472150.KS", qty: 215, avg: 95108, account: "일반" },
    { name: "현대차2우B", code: "005387.KS", qty: 60, avg: 248000, account: "일반" },
    { name: "삼성전자", code: "005930.KS", qty: 55, avg: 269454, account: "일반" },
    { name: "두산에너빌리티", code: "034020.KS", qty: 68, avg: 95108, account: "일반" },
    { name: "삼성SDI", code: "006400.KS", qty: 12, avg: 510791, account: "일반" },
    { name: "AAPL", code: "AAPL", qty: 10, avg: 117.0, account: "일반" },
    { name: "TIGER 배당커버드콜액티브", code: "472150.KS", qty: 243, avg: 29545, account: "ISA" },
    { name: "TIME 미국나스닥100액티브", code: "453850.KS", qty: 30, avg: 13000, account: "ISA" },
    { name: "TIGER 배당커버드콜액티브", code: "472150.KS", qty: 250, avg: 10000, account: "IRP" },
    { name: "KODEX 삼성전자SK하이닉스채권혼합50", code: "0177N0.KS", qty: 100, avg: 14145, account: "IRP" },
    { name: "TIGER 미국나스닥100타겟데일리커버드콜", code: "486290.KS", qty: 100, avg: 11080, account: "연금저축" }
];

// holdings.json 로드 또는 초기화
function loadHoldings() {
    try {
        if (fs.existsSync(HOLDINGS_FILE)) {
            const fileContent = fs.readFileSync(HOLDINGS_FILE, 'utf-8');
            return JSON.parse(fileContent);
        }
    } catch (e) {
        console.error("holdings.json 로드 실패:", e);
    }
    // 기본 데이터로 새 파일 생성
    saveHoldings(DEFAULT_HOLDINGS);
    return DEFAULT_HOLDINGS;
}

// holdings.json 저장
function saveHoldings(holdings) {
    try {
        fs.writeFileSync(HOLDINGS_FILE, JSON.stringify(holdings, null, 2), 'utf-8');
    } catch (e) {
        console.error("holdings.json 저장 실패:", e);
    }
}

// data.json (실시간 수집 데이터) 로드
function loadCollectedData() {
    try {
        if (fs.existsSync(DATA_FILE)) {
            return JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8'));
        }
    } catch (e) {
        console.error("data.json 로드 실패:", e);
    }
    return { exchangeRate: 1350.0, stocks: {} };
}

// 특정 종목의 가격 및 배당 정보 조회
function getStockInfo(item, collectedData) {
    // 사용자가 가격/배당금을 직접 수동 입력한 종목인 경우
    if (item.isManual) {
        const price = Number(item.price) || 0;
        const divPerShare = Number(item.divPerShare) || 0;
        const currency = item.currency || 'KRW';
        const calculatedYield = price > 0 ? ((divPerShare / price) * 100).toFixed(1) + '%' : '0.0%';
        return {
            price,
            divPerShare,
            currency,
            months: item.months || [1,2,3,4,5,6,7,8,9,10,11,12],
            officialYield: calculatedYield,
            targetYield: calculatedYield
        };
    }

    const rawCode = (item.code || "").toUpperCase();
    const cleanCode = rawCode.replace('.KS', '').replace('.KQ', '');
    
    let price = 0;
    let divPerShare = 0;
    let currency = 'KRW';
    let months = [];

    // 1. data.json 에서 먼저 조회
    let stockData = null;
    if (collectedData && collectedData.stocks) {
        stockData = collectedData.stocks[rawCode] || collectedData.stocks[cleanCode];
    }

    if (stockData) {
        price = stockData.price || 0;
        divPerShare = stockData.divPerShare || 0;
        currency = stockData.currency || 'KRW';
        months = stockData.months || [];
    } else {
        // 2. data.json에 없으면 BACKUP_STOCKS 백업 데이터 활용
        const backup = BACKUP_STOCKS[rawCode] || BACKUP_STOCKS[cleanCode];
        if (backup) {
            price = backup.price || 0;
            divPerShare = backup.divPerShare || 0;
            currency = backup.currency || 'KRW';
            months = backup.months || [];
        }
    }

    // 배당수익률 및 목표배당수익률 계산
    let calculatedYield = price > 0 ? ((divPerShare / price) * 100).toFixed(1) + '%' : '0.0%';
    let officialYield = calculatedYield;
    let targetYield = calculatedYield;

    // 특정 ETF 상품들의 목표 배당률 고정 보정값 (백업 정보 반영)
    const backup = BACKUP_STOCKS[rawCode] || BACKUP_STOCKS[cleanCode];
    if (backup) {
        if (backup.officialYield) officialYield = backup.officialYield;
        if (backup.targetYield) targetYield = backup.targetYield;
    }

    return {
        price,
        divPerShare,
        currency,
        months: months.length > 0 ? months : [1,2,3,4,5,6,7,8,9,10,11,12],
        officialYield,
        targetYield
    };
}

// 1. 전체 포트폴리오 조회 API
app.get('/tools/get-portfolio', (req, res) => {
    const holdings = loadHoldings();
    const collectedData = loadCollectedData();
    const exchangeRate = collectedData.exchangeRate || 1350.0;

    let totalInvestKRW = 0;
    let totalEvalKRW = 0;
    let totalAnnualDivKRW = 0;

    const list = holdings.map((item, index) => {
        const info = getStockInfo(item, collectedData);
        const isUSD = info.currency === 'USD';

        const priceKRW = isUSD ? Math.round(info.price * exchangeRate) : info.price;
        const divKRW = isUSD ? (info.divPerShare * exchangeRate) : info.divPerShare;
        const investKRW = isUSD ? (item.qty * item.avg * exchangeRate) : (item.qty * item.avg);
        const evalKRW = item.qty * priceKRW;
        
        const isTaxFreeAccount = ['ISA', 'IRP', '연금저축'].includes(item.account);
        const taxFactor = isTaxFreeAccount ? 1.0 : 0.846; // 일반 계좌는 15.4% 원천징수 반영
        const annualDivKRW = item.qty * divKRW * taxFactor;

        totalInvestKRW += investKRW;
        totalEvalKRW += evalKRW;
        totalAnnualDivKRW += annualDivKRW;

        return {
            id: index,
            name: item.name || info.name || item.code,
            code: item.code,
            account: item.account,
            qty: item.qty,
            avg: item.avg,
            price: priceKRW,
            officialYield: info.officialYield,
            targetYield: info.targetYield,
            annualDivKRW: Math.round(annualDivKRW),
            investKRW: Math.round(investKRW),
            evalKRW: Math.round(evalKRW),
            months: info.months,
            isManual: item.isManual,
            manualPrice: item.price,
            manualDivPerShare: item.divPerShare,
            manualCurrency: item.currency
        };
    });

    const totalProfitKRW = totalEvalKRW - totalInvestKRW;
    const totalReturnRate = totalInvestKRW > 0 ? ((totalProfitKRW / totalInvestKRW) * 100).toFixed(2) + '%' : '0.00%';
    const totalYieldRate = totalInvestKRW > 0 ? ((totalAnnualDivKRW / totalInvestKRW) * 100).toFixed(2) + '%' : '0.00%';

    res.json({
        success: true,
        summary: {
            totalInvestKRW: Math.round(totalInvestKRW),
            totalEvalKRW: Math.round(totalEvalKRW),
            totalProfitKRW: Math.round(totalProfitKRW),
            totalReturnRate,
            totalAnnualDivKRW: Math.round(totalAnnualDivKRW),
            totalYieldRate,
            exchangeRate
        },
        holdings: list
    });
});

// 2. 종목 추가 API
app.post('/tools/add-stock', (req, res) => {
    const { name, code, qty, avg, account, isManual, price, divPerShare, currency } = req.body;
    if (!qty || !avg) return res.status(400).json({ success: false, message: "수량과 평단가는 필수입니다." });

    const holdings = loadHoldings();
    const newStock = { 
        name: name || code || "미지정 종목", 
        code: code || "", 
        qty: Number(qty), 
        avg: Number(avg), 
        account: account || "일반" 
    };

    if (isManual) {
        newStock.isManual = true;
        newStock.price = Number(price) || 0;
        newStock.divPerShare = Number(divPerShare) || 0;
        newStock.currency = currency || 'KRW';
    }

    holdings.push(newStock);
    saveHoldings(holdings);

    res.json({ success: true, message: "종목이 성공적으로 추가되었습니다.", added: newStock });
});

// 3. 종목 수정 API
app.post('/tools/update-stock', (req, res) => {
    const { id, name, code, qty, avg, account, isManual, price, divPerShare, currency } = req.body;
    const holdings = loadHoldings();
    
    if (id === undefined || id < 0 || id >= holdings.length) {
        return res.status(400).json({ success: false, message: "유효하지 않은 ID입니다." });
    }

    const updatedStock = {
        name: name || holdings[id].name,
        code: code || holdings[id].code,
        qty: Number(qty),
        avg: Number(avg),
        account: account || holdings[id].account
    };

    if (isManual) {
        updatedStock.isManual = true;
        updatedStock.price = Number(price) || 0;
        updatedStock.divPerShare = Number(divPerShare) || 0;
        updatedStock.currency = currency || 'KRW';
    }

    holdings[id] = updatedStock;

    saveHoldings(holdings);
    res.json({ success: true, message: "종목 정보가 수정되었습니다." });
});

// 4. 종목 삭제 API
app.post('/tools/delete-stock', (req, res) => {
    const { id } = req.body;
    const holdings = loadHoldings();

    if (id === undefined || id < 0 || id >= holdings.length) {
        return res.status(400).json({ success: false, message: "유효하지 않은 ID입니다." });
    }

    const removed = holdings.splice(id, 1);
    saveHoldings(holdings);

    res.json({ success: true, message: "종목이 삭제되었습니다.", removed });
});

app.get('/', (req, res) => res.send("RuleFit API Server is running"));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
