const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// GitHub Auto-Commit 설정
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_REPO = "pabusu84/RuleFit";
const FILE_PATH = "server/server.js";

// 주식 및 배당 기초 데이터 (공시 배당률 vs 실제 목표 배당률)
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

// 📌 [기존 이미지 기반 15개 전체 보유 목록 영구 고정]
let holdings = [
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

const EXCHANGE_RATE = 1350;

// GitHub 코드 자동 Commit/Push 처리 함수
async function saveToGitHub() {
    if (!GITHUB_TOKEN) return;
    try {
        const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${FILE_PATH}`;
        const getFile = await fetch(url, {
            headers: { 'Authorization': `token ${GITHUB_TOKEN}`, 'User-Agent': 'RuleFit-App' }
        });
        const fileData = await getFile.json();
        
        const fs = require('fs');
        let currentCode = fs.readFileSync(__filename, 'utf8');
        const updatedHoldingsStr = `let holdings = ${JSON.stringify(holdings, null, 4)};`;
        const updatedCode = currentCode.replace(/let holdings = \[[\s\S]*?\];/, updatedHoldingsStr);

        const body = {
            message: "Auto-update holdings via API",
            content: Buffer.from(updatedCode).toString('base64'),
            sha: fileData.sha
        };

        await fetch(url, {
            method: 'PUT',
            headers: { 
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Content-Type': 'application/json',
                'User-Agent': 'RuleFit-App'
            },
            body: JSON.stringify(body)
        });
    } catch (error) {
        console.error("GitHub Auto-Commit 실패:", error);
    }
}

// 1. 전체 포트폴리오 조회 API
app.get('/tools/get-portfolio', (req, res) => {
    let totalInvestKRW = 0;
    let totalEvalKRW = 0;
    let totalAnnualDivKRW = 0;

    const list = holdings.map((item, index) => {
        const rawCode = (item.code || "").toUpperCase();
        const info = BACKUP_STOCKS[rawCode] || { price: item.avg, divPerShare: 0 };
        const isUSD = info.currency === 'USD';

        const priceKRW = isUSD ? Math.round(info.price * EXCHANGE_RATE) : info.price;
        const divKRW = isUSD ? (info.divPerShare * EXCHANGE_RATE) : info.divPerShare;
        const investKRW = isUSD ? (item.qty * item.avg * EXCHANGE_RATE) : (item.qty * item.avg);
        const evalKRW = item.qty * priceKRW;
        
        const isTaxFreeAccount = ['ISA', 'IRP', '연금저축'].includes(item.account);
        const taxFactor = isTaxFreeAccount ? 1.0 : 0.846;
        const annualDivKRW = item.qty * divKRW * taxFactor;

        totalInvestKRW += investKRW;
        totalEvalKRW += evalKRW;
        totalAnnualDivKRW += annualDivKRW;

        return {
            id: index,
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

// 2. 종목 추가 API
app.post('/tools/add-stock', async (req, res) => {
    const { name, code, qty, avg, account } = req.body;
    if (!qty || !avg) return res.status(400).json({ success: false, message: "수량과 평단가는 필수입니다." });

    const newStock = { name: name || code || "미지정 종목", code: code || "", qty: Number(qty), avg: Number(avg), account: account || "일반" };
    holdings.push(newStock);
    await saveToGitHub();

    res.json({ success: true, message: "종목이 성공적으로 추가되어 저장되었습니다.", added: newStock });
});

// 3. 종목 수정 API
app.post('/tools/update-stock', async (req, res) => {
    const { id, name, code, qty, avg, account } = req.body;
    if (id === undefined || id < 0 || id >= holdings.length) return res.status(400).json({ success: false, message: "유효하지 않은 ID입니다." });

    holdings[id] = {
        name: name || holdings[id].name,
        code: code || holdings[id].code,
        qty: Number(qty),
        avg: Number(avg),
        account: account || holdings[id].account
    };

    await saveToGitHub();
    res.json({ success: true, message: "종목 정보가 수정되었습니다." });
});

// 4. 종목 삭제 API
app.post('/tools/delete-stock', async (req, res) => {
    const { id } = req.body;
    if (id === undefined || id < 0 || id >= holdings.length) return res.status(400).json({ success: false, message: "유효하지 않은 ID입니다." });

    const removed = holdings.splice(id, 1);
    await saveToGitHub();

    res.json({ success: true, message: "종목이 삭제되었습니다.", removed });
});

app.get('/', (req, res) => res.send("RuleFit REST API Server is running"));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
