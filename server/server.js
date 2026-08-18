const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// 주식 및 배당 기초 데이터
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
    "GPIX": { name: "GPIX", price: 54.96, divPerShare: 5.4, officialYield: "9.8%", targetYield: "9.8%", currency: "USD" },
    "JEPQ": { name: "JEPQ", price: 57.09, divPerShare: 5.04, officialYield: "8.8%", targetYield: "8.8%", currency: "USD" },
    "AAPL": { name: "AAPL", price: 220.0, divPerShare: 1.0, officialYield: "0.5%", targetYield: "0.5%", currency: "USD" }
};

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

// 1. 포트폴리오 전체 조회 API (GET)
app.get('/tools/get-portfolio', (req, res) => {
    let totalInvestKRW = 0;
    let totalEvalKRW = 0;
    let totalAnnualDivKRW = 0;

    const list = holdings.map(item => {
        const rawCode = (item.code || "").toUpperCase();
        const info = BACKUP_STOCKS[rawCode] || { price: item.avg, divPerShare: 0 };
        const isUSD = info.currency === 'USD';

        const priceKRW = isUSD ? Math.round(info.price * EXCHANGE_RATE) : info.price;
        const divKRW = isUSD ? (info.divPerShare * EXCHANGE_RATE) : info.divPerShare;
        const investKRW = isUSD ? (item.qty * item.avg * EXCHANGE_RATE) : (item.qty * item.avg);
        const evalKRW = item.qty * priceKRW;
        const taxFactor = (item.account === 'ISA') ? 1.0 : 0.846;
        const annualDivKRW = item.qty * divKRW * taxFactor;

        totalInvestKRW += investKRW;
        totalEvalKRW += evalKRW;
        totalAnnualDivKRW += annualDivKRW;

        return {
            name: item.name,
            code: item.code,
            account: item.account,
            qty: item.qty,
            avg: item.avg,
            officialYield: info.officialYield || "-",
            targetYield: info.targetYield || "-",
            annualDivKRW: Math.round(annualDivKRW),
            investKRW: Math.round(investKRW)
        };
    });

    const totalProfitKRW = totalEvalKRW - totalInvestKRW;
    const totalReturnRate = totalInvestKRW > 0 ? ((totalProfitKRW / totalInvestKRW) * 100).toFixed(2) + '%' : '0%';
    const totalYieldRate = totalInvestKRW > 0 ? ((totalAnnualDivKRW / totalInvestKRW) * 100).toFixed(2) + '%' : '0%';

    res.json({
        success: true,
        summary: {
            totalInvestKRW: Math.round(totalInvestKRW),
            totalEvalKRW: Math.round(totalEvalKRW),
            totalProfitKRW: Math.round(totalProfitKRW),
            totalReturnRate,
            totalAnnualDivKRW: Math.round(totalAnnualDivKRW),
            totalYieldRate
        },
        holdings: list
    });
});

// 2. 종목 추가 API (POST)
app.post('/tools/add-stock', (req, res) => {
    const { name, code, qty, avg, account } = req.body;
    if (!qty || !avg) {
        return res.status(400).json({ success: false, message: "수량(qty)과 평단가(avg)는 필수입니다." });
    }

    const newStock = {
        name: name || code || "미지정 종목",
        code: code || "",
        qty: Number(qty),
        avg: Number(avg),
        account: account || "일반"
    };

    holdings.push(newStock);
    res.json({ success: true, message: "종목이 성공적으로 추가되었습니다.", added: newStock });
});

app.get('/', (req, res) => res.send("RuleFit REST API Server is running"));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
