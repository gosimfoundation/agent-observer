# 智能体巡天黑客松 · Agentic Cosmos

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

公开文案全部在 `src/i18n/zh.ts` 与 `src/i18n/en.ts`。赛程与奖金以团队版赛事安排为准；
报名方式及现场邀请规模仍待确定。

网站对标结论、分阶段改进方案与待确认数据见
[`docs/goaihz-benchmark-and-improvement-plan.md`](docs/goaihz-benchmark-and-improvement-plan.md)。

## 与其它站点的差异

报名、登录和组队流程沿用 Factory26，但必须连接赛事独立的 Supabase 项目。先在该项目执行
`supabase/migrations/20260820_00_cosmos26_registration.sql`，再配置 `.env` 中的
`VITE_SUPABASE_URL` 与 `VITE_SUPABASE_ANON_KEY`。不要复用 Factory26 的数据库凭据。

最终测评与排行榜由 CosmosBench 支撑。配置 `VITE_COSMOSBENCH_URL` 与
`VITE_COSMOSBENCH_LEADERBOARD_API`；接口可直接返回数组，也可返回 `{ entries: [...] }` 或
`{ data: [...] }`。若接口不可用，站点会尝试读取 `public/cosmosbench-leaderboard.json` 快照。

## 报名与组队

`/register` 提供 Supabase Auth 注册、登录、密码重置、队伍创建与加入。在独立的
赛事独立的 Supabase 项目中按文件名顺序执行 `supabase/migrations/` 下的所有 SQL：

1. `20260820_00_cosmos26_registration.sql`
2. `20260820_01_cosmos26_team_workflow.sql`

第二个迁移使队伍创建、加入、退出与解散在数据库事务中完成，并防止客户端绕过人数上限。
