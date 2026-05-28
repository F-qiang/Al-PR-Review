# AI PR Review 助手

基于 GitHub Pull Request 与 LLM 的智能代码评审工具，适用于七牛云比赛项目。

## 功能

- 输入 GitHub PR 链接，自动拉取变更
- AI 生成变更摘要、风险识别、Review 建议
- 规则引擎预筛（硬编码密钥、SQL 拼接、eval 等）
- SSE 流式展示分析过程
- 分析历史记录

## 项目结构

```
├── backend/          # FastAPI 后端
├── frontend/         # Next.js 前端
├── docs/             # 架构设计文档
└── 题目.ini
```

## 快速开始

### 1. 后端

```bash
cd backend
copy .env.example .env
# 编辑 .env，填入 LLM_API_KEY

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

浏览器打开 http://localhost:3000

## 环境变量

| 变量 | 说明 |
|------|------|
| `LLM_API_KEY` | LLM API 密钥（必填） |
| `LLM_BASE_URL` | OpenAI 兼容接口地址，默认 DeepSeek |
| `LLM_MODEL` | 模型名称 |
| `GITHUB_TOKEN` | GitHub Token（可选，私有仓库/API 限额） |

## 演示 PR 示例

公开 PR 可直接分析，例如：

- `https://github.com/python/cpython/pull/1`（示例格式）
- 或任意公开仓库的 PR 链接

## 开发进度

- [x] MVP：PR 拉取 + LLM 分析 + 流式前端
- [x] 规则引擎预筛
- [x] 分析历史
- [ ] 七牛云 OSS 报告存储
- [ ] GitHub App Webhook 自动 Review
- [ ] 大 PR 分块并行分析

## 技术栈

- **后端**：FastAPI、SQLAlchemy、httpx、SQLite
- **前端**：Next.js 16、TypeScript、Tailwind CSS
- **AI**：OpenAI 兼容 API（DeepSeek / 通义 / GPT）
