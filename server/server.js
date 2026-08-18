const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

// ==========================================
// 🔒 API Key 보안 검증 미들웨어
// ==========================================
const API_KEY = process.env.API_KEY || "rulefit-secret-key-2026"; // PlayMCP에 입력할 Value값

app.use((req, res, next) => {
    const clientKey = req.headers['x-api-key'];
    
    // API 키가 일치하지 않으면 접근 거부
    if (!clientKey || clientKey !== API_KEY) {
        return res.status(401).json({ 
            success: false, 
            message: "Unauthorized: 올바른 API Key가 필요합니다." 
        });
    }
    next();
});

// 종목명 매핑
const STOCK_MAP = {
    "462330.KS": "TIME 미국나스닥100액티브",
    "426030.KS": "TIME 미국나스닥100액티브",
    "486290.KS": "TIGER 미국나스닥100타겟데일리커버드콜",
    "0177N0.KS": "KODEX 삼성전자SK하이닉스채권혼합50",
    "0177NO.KS": "KODEX 삼성전자SK하이닉스채권혼합50",
    "005930.KS": "삼성전자",
    "005935.KS": "삼성전자우",
    "000660.KS": "SK하이닉스",
    "006400.KS": "삼성SDI",
    "005387.KS": "현대차2우B",
    "034020.KS": "두산에너빌리티",
    "472150.KS": "TIGER 배당커버드콜액티브"
};

// 백업 기초 데이터 (시세, 주당 배당금, 공시 배당률, 실제 연환산 배당률)
const BACKUP_STOCKS = {
    "005930.KS": { name: "삼성전자", price: 60000, divPerShare: 1444, months: [4,5,8,11], currency: "KRW", officialYield: "2.4%", targetYield: "2.4%" },
    "005935.KS": { name: "삼성전자우", price: 50000, divPerShare: 1445, months: [4,5,8,11], currency: "KRW", officialYield: "2.9%", targetYield: "2.9%" },
    "000660.KS": { name: "SK하이닉스", price: 180000, divPerShare: 1500, months: [4,5,8,11], currency: "KRW", officialYield: "0.8%", targetYield: "0.8%" },
    "006400.KS": { name: "삼성SDI", price: 350000, divPerShare: 1000, months: [4], currency: "KRW", officialYield: "0.3%", targetYield: "0.3%" },
    "005387.KS": { name: "현대차2우B", price: 150000, divPerShare: 11500, months: [4,5,8,11], currency: "KRW", officialYield: "7.6%", targetYield: "7.6%" },
    "034020.KS": { name: "두산에너빌리티", price: 20000, divPerShare: 0, months: [], currency: "KRW", officialYield: "0.0%", targetYield: "0.0%" },
    "472150.KS": { name: "TIGER 배당커버드콜액티브", price: 10000, divPerShare: 70 * 12, months: [1,2,3,4,5,6,7,8,9,10,11,12], currency: "KRW", officialYield: "4.2%", targetYield: "8.4%" },
    "486290.KS": { name: "TIGER 미국나스닥100타겟데일리커버드콜", price: 11080, divPerShare: 100 * 12, months: [1,2,3,4,5,6,7,8,9,10,11,12], currency: "KRW", officialYield: "2.1%", targetYield: "10.8%" },
    "0177N0.KS": { name: "KODEX 삼성전자SK하이닉스채권혼합50", price: 14145, divPerShare: 350, months: [1,4,7,10], currency: "KRW", officialYield: "2.5%", targetYield: "2.5%" },
    "GPIX": { name: "GPIX", price: 54.96, divPerShare: 0.45 * 12, months: [1,2,3,4,5,6,7,8,9,10,11,12], currency: "USD", officialYield: "9.8%", targetYield: "9.8%" },
    "JEPQ": { name: "JEPQ", price: 57.09, divPerShare: 0.42 * 12, months: [1,2,3,4,5,6,7,8,9,10,11,12], currency: "USD", officialYield: "8.8%", targetYield: "8.8%" },
    "AAPL": { name: "AAPL", price: 220.0, divPerShare: 0.25 * 4, months: [2,5,8,11], currency: "USD", officialYield: "0.5%", targetYield: "0.5%" }
};

// 기본 보유 종목 리스트
let holdings = [
    { name: "삼성전자", code: "005930.KS", qty: 55, avg: 269454, account: "일반" },
    { name: "GPIX", code: "GPIX", qty: 287, avg: 54.96, account: "일반" },
    { name: "JEPQ", code: "JEPQ", qty: 373, avg: 57.09, account: "일반" },
    { name: "삼성전자우", code: "005935.KS", qty: 400, avg: 188396, account: "일반" },
    { name: "SK하이닉스", code: "000660.KS", qty: 30, avg: 2162833, account: "일반" },
    { name: "삼성SDI", code: "006400.KS", qty: 12, avg: 510791, account: "일반" },
    { name: "현대차2우B", code: "005387.KS", qty: 60, avg: 248000, account: "일반" },
    { name: "두산에너빌리티", code: "034020.KS", qty: 68, avg: 95108, account: "일반" },
    { name: "TIGER 배당커버드콜액티브", code: "472150.KS", qty: 215, avg: 95108, account: "일반" },
    { name: "TIGER 배당커버드콜액티브", code: "472150.KS", qty: 243, avg: 29545, account: "ISA" },
    { name: "AAPL", code: "AAPL", qty: 10, avg: 117.0, account: "일반" }
];

const EXCHANGE_RATE = 1350;

// [MCP Tool 1] 포트폴리오 요약 및 배당금 계산 반환
app.get('/tools/get-portfolio', (req, res) => {
    let totalInvest = 0;
    let totalEval = 0;
    let totalDiv = 0;

    const processedList = holdings.map(item => {
        const rawCode = (item.code || "").toUpperCase();
        const info = BACKUP_STOCKS[rawCode] || { price: item.avg, divPerShare: 0, currency: "KRW", officialYield: "-", targetYield: "-" };
        const isUSD = info.currency === 'USD' || ['GPIX', 'JEPQ', 'AAPL'].includes(rawCode);

        const priceKRW = isUSD ? Math.round(info.price * EXCHANGE_RATE) : info.price;
        const divKRWPerShare = isUSD ? (info.divPerShare * EXCHANGE_RATE) : info.divPerShare;
        
        const investKRW = isUSD ? (item.qty * item.avg * EXCHANGE_RATE) : (item.qty * item.avg);
        const evalKRW = item.qty * priceKRW;
        
        const taxFactor = (['ISA', 'IRP', '연금저축'].includes(item.account)) ? 1.0 : 0.846;
        const annualDivKRW = item.qty * divKRWPerShare * taxFactor;

        totalInvest += investKRW;
        totalEval += evalKRW;
        totalDiv += annualDivKRW;

        return {
            name: STOCK_MAP[rawCode] || item.name,
            account: item.account,
            qty: item.qty,
            avg: item.avg,
            officialYield: info.officialYield, // 증권사 공시 배당률
            targetYield: info.targetYield,     // 실제 지급 기준 연환산 배당률
            annualDivKRW: Math.round(annualDivKRW),
            investKRW: Math.round(investKRW)
        };
    });

    const totalProfit = totalEval - totalInvest;
    const totalReturnRate = totalInvest > 0 ? ((totalProfit / totalInvest) * 100).toFixed(2) : "0.00";
    const totalYieldRate = totalInvest > 0 ? ((totalDiv / totalInvest) * 100).toFixed(2) : "0.00";

    res.json({
        success: true,
        summary: {
            totalInvestKRW: Math.round(totalInvest),
            totalEvalKRW: Math.round(totalEval),
            totalProfitKRW: Math.round(totalProfit),
            totalReturnRate: `${totalReturnRate}%`,
            totalAnnualDivKRW: Math.round(totalDiv),
            totalYieldRate: `${totalYieldRate}%`
        },
        holdings: processedList
    });
});

// [MCP Tool 2] 자연어 명령을 통한 종목 추가
app.post('/tools/add-stock', (req, res) => {
    let { name, code, qty, avg, account } = req.body;

    if (!code && !name) {
        return res.status(400).json({ success: false, message: "종목명 또는 코드가 필요합니다." });
    }

    let searchCode = (code || name).toUpperCase();
    if (/^[0-9]{6}$/.test(searchCode)) {
        searchCode = searchCode + '.KS';
    }

    const cleanCode = searchCode.replace('.KS', '');
    const stockName = STOCK_MAP[searchCode] || STOCK_MAP[cleanCode] || name || searchCode;

    const newStock = {
        name: stockName,
        code: searchCode,
        qty: Number(qty),
        avg: Number(avg),
        account: account || "일반"
    };

    holdings.push(newStock);

    res.json({
        success: true,
        message: `${stockName} (${newStock.account}) ${qty}주가 성공적으로 추가되었습니다.`,
        addedStock: newStock
    });
});

// [MCP Tool 3] 알림 메시지 생성
app.get('/tools/dividend-alert', (req, res) => {
    let totalDiv = 0;
    holdings.forEach(item => {
        const info = BACKUP_STOCKS[item.code] || { divPerShare: 0 };
        const taxFactor = (['ISA', 'IRP', '연금저축'].includes(item.account)) ? 1.0 : 0.846;
        totalDiv += item.qty * info.divPerShare * taxFactor * (info.currency === 'USD' ? EXCHANGE_RATE : 1);
    });

    res.json({
        success: true,
        message: `📢 [Rulefit] 연간 예상 실수령 배당금은 약 ${Math.round(totalDiv).toLocaleString()}원 입니다.`
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Rulefit MCP Server running on port ${PORT}`));
