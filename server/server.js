const express = require('express');
const cors = require('cors');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { SSEServerTransport } = require('@modelcontextprotocol/sdk/server/sse.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');

const app = express();

// PlayMCP 통신을 위한 CORS 풀기
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'x-api-key', 'Accept']
}));

app.use(express.json());

// MCP 서버 인스턴스 생성
const mcpServer = new Server(
    { name: "rulefit-mcp", version: "1.0.0" },
    { capabilities: { tools: {} } }
);

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

// 1. PlayMCP Tools 목록
mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "get_portfolio",
                description: "보유 주식 포트폴리오의 평가 금액, 수익률 및 연간 배당금을 조회합니다.",
                inputSchema: { type: "object", properties: {} }
            },
            {
                name: "add_stock",
                description: "포트폴리오에 새로운 주식을 추가합니다.",
                inputSchema: {
                    type: "object",
                    properties: {
                        name: { type: "string", description: "종목명" },
                        code: { type: "string", description: "종목코드" },
                        qty: { type: "number", description: "수량" },
                        avg: { type: "number", description: "평단가" },
                        account: { type: "string", description: "계좌종류" }
                    },
                    required: ["qty", "avg"]
                }
            }
        ]
    };
});

// 2. Tool 실행 핸들러
mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    if (name === "get_portfolio") {
        let totalInvest = 0;
        let totalEval = 0;
        let totalDiv = 0;

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

            totalInvest += investKRW;
            totalEval += evalKRW;
            totalDiv += annualDivKRW;

            return `${item.name} (${item.account}): ${item.qty}주 / 예상배당: ${Math.round(annualDivKRW).toLocaleString()}원 (실제 목표 배당률: ${info.targetYield || '-'})`;
        });

        const resultText = `[RuleFit 포트폴리오 요약]\n- 총 투자금: ${Math.round(totalInvest).toLocaleString()}원\n- 총 평가금: ${Math.round(totalEval).toLocaleString()}원\n- 연간 실수령 배당금: ${Math.round(totalDiv).toLocaleString()}원\n\n[보유 종목]\n` + list.join('\n');

        return { content: [{ type: "text", text: resultText }] };
    }

    if (name === "add_stock") {
        holdings.push({
            name: args.name || args.code,
            code: args.code || "",
            qty: Number(args.qty),
            avg: Number(args.avg),
            account: args.account || "일반"
        });
        return { content: [{ type: "text", text: `${args.name || args.code} ${args.qty}주가 정상적으로 추가되었습니다.` }] };
    }

    throw new Error("Tool not found");
});

// SSE 세션 Map 관리
const transports = new Map();

app.get('/sse', async (req, res) => {
    // SSE 헤더 설정
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const transport = new SSEServerTransport('/message', res);
    transports.set(transport.sessionId, transport);

    req.on('close', () => {
        transports.delete(transport.sessionId);
    });

    await mcpServer.connect(transport);
});

app.post('/message', async (req, res) => {
    const sessionId = req.query.sessionId;
    const transport = transports.get(sessionId);

    if (transport) {
        await transport.handlePostMessage(req, res);
    } else {
        res.status(400).send("Session not found or expired");
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`MCP Server running on port ${PORT}`));
