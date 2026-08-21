# 巡天开源智能体黑客松 · Open Survey Agent Hackathon

GOSIM 黑客松站点，面向智能巡天运行。参赛者提交一个观测智能体：读取夜空状态，
在每 900 秒的时隙里决定观测哪个天区，或者等待。

内容源自 `cosmos-hackathon/开放巡天智能体挑战赛-中文版.html`，站点结构沿用
`events/oaic-harness-2026`。

## 本地开发

```bash
npm install
npm run dev
```

从仓库根目录：`npm run dev:agentic-cosmos-2026`

## 内容位置

公开文案全部在 `src/i18n/zh.ts` 与 `src/i18n/en.ts`。赛程、赛题与报名方式尚未确定，
页面上一律标「待定」——未确定的事不写死。

## 与其它站点的差异

报名、登录和组队流程沿用 Factory26，但必须连接独立的 Cosmos26 Supabase 项目。先在该项目执行
`supabase/migrations/20260820_00_cosmos26_registration.sql`，再配置 `.env` 中的
`VITE_SUPABASE_URL` 与 `VITE_SUPABASE_ANON_KEY`。不要复用 Factory26 的数据库凭据。

最终测评与排行榜由 CosmosBench 支撑。配置 `VITE_COSMOSBENCH_URL` 与
`VITE_COSMOSBENCH_LEADERBOARD_API`；接口可直接返回数组，也可返回 `{ entries: [...] }` 或
`{ data: [...] }`。若接口不可用，站点会尝试读取 `public/cosmosbench-leaderboard.json` 快照。
