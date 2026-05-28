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
│   ├── 架构设计.md
│   └── 演示指南.md   # 比赛演示脚本
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

比赛演示流程见 [docs/演示指南.md](docs/演示指南.md)

## 环境变量

| 变量 | 说明 |
|------|------|
| `LLM_API_KEY` | LLM API 密钥（必填） |
| `LLM_BASE_URL` | OpenAI 兼容接口地址，默认 DeepSeek |
| `LLM_MODEL` | 模型名称 |
| `GITHUB_TOKEN` | GitHub Token（可选，私有仓库/API 限额） |
| `GITHUB_WEBHOOK_SECRET` | Webhook 签名密钥（可选） |
| `GITHUB_AUTO_COMMENT` | 分析完成后自动回评 PR，默认 `true` |
| `QINIU_ACCESS_KEY` | 七牛云 Access Key（可选） |
| `QINIU_SECRET_KEY` | 七牛云 Secret Key（可选） |
| `QINIU_BUCKET` | 七牛云存储空间名称（可选） |
| `QINIU_DOMAIN` | 七牛云 CDN 域名（可选） |

## 演示 PR 示例

公开 PR 可直接分析，例如：

- `https://github.com/python/cpython/pull/1`（示例格式）
- 或任意公开仓库的 PR 链接

## 开发进度

- [x] MVP：PR 拉取 + LLM 分析 + 流式前端
- [x] 规则引擎预筛
- [x] 分析历史
- [x] 大 PR 分块并行分析
- [x] Markdown 报告导出
- [x] 七牛云 OSS 报告存储（可选，配置 QINIU_* 后启用）
- [x] GitHub Webhook 自动 Review

## GitHub Webhook 配置

1. 仓库 Settings → Webhooks → Add webhook
2. Payload URL：`https://你的域名/api/v1/webhooks/github`
3. Content type：`application/json`
4. Secret：与 `GITHUB_WEBHOOK_SECRET` 保持一致
5. 事件：勾选 **Pull requests**
6. PR 打开或更新时会自动创建分析任务

## 技术栈

- **后端**：FastAPI、SQLAlchemy、httpx、SQLite
- **前端**：Next.js 16、TypeScript、Tailwind CSS
- **AI**：OpenAI 兼容 API（DeepSeek / 通义 / GPT）
