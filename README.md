# AI PR Review 助手

基于 GitHub Pull Request 与大模型的智能代码评审工具。支持输入 PR 链接后自动拉取代码变更，生成变更摘要、风险识别、Review 建议，并输出 Markdown 报告；同时支持历史记录分页、状态筛选、Webhook 自动触发、PR 自动评论、七牛云报告上传，以及演示模式兜底。

## 核心功能

- 输入 GitHub PR 链接，自动拉取变更
- AI 生成变更摘要、风险识别、Review 建议
- 规则引擎预筛：硬编码密钥、SQL 拼接、`eval` 等常见风险
- SSE 流式展示分析过程
- 分析历史记录分页与状态筛选
- 同一 PR 幂等保护，避免重复创建任务
- Webhook 自动创建分析任务
- 分析完成后自动评论 PR
- Markdown 报告导出
- 七牛云对象存储报告上传
- 统一错误响应
- 数据库索引优化
- 演示模式支持固定示例结果
- 失败重试与任务复用提示

## 技术栈

- 后端：FastAPI、SQLAlchemy、SQLite、SSE
- 前端：Next.js 16、TypeScript、Tailwind CSS
- AI：OpenAI 兼容接口
- 自动化：GitHub Actions、PowerShell 脚本

## 项目结构

```
├── backend/          # FastAPI 后端
├── frontend/         # Next.js 前端
├── docs/             # 架构设计文档
│   ├── 架构设计.md
│   ├── 演示指南.md   # 比赛演示脚本
│   └── 测试清单.md   # 项目测试清单
└── 题目.ini
```

## 快速开始

### 1. 后端

```powershell
cd backend
copy .env.example .env
# 编辑 .env，填入 LLM_API_KEY

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

后端接口文档：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 2. 前端

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

浏览器打开 http://localhost:3000

### 3. 一键启动脚本（Windows PowerShell）

已提供演示启动脚本：

```powershell
.\scripts\start_backend.ps1
```

另开一个 PowerShell：

```powershell
.\scripts\start_frontend.ps1
```

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
| `DEMO_MODE` | 演示模式开关，`true` 时返回固定示例结果 |
| `QINIU_ACCESS_KEY` | 七牛云 Access Key（可选） |
| `QINIU_SECRET_KEY` | 七牛云 Secret Key（可选） |
| `QINIU_BUCKET` | 七牛云存储空间名称（可选） |
| `QINIU_DOMAIN` | 七牛云 CDN 域名（可选） |
| `DATABASE_URL` | SQLite 数据库连接地址，推荐固定使用 `backend/prreview.db` |

## 演示 PR 示例

公开 PR 可直接分析，例如：

- `https://github.com/python/cpython/pull/1`（已验证可用于演示）
- 或任意公开仓库的 PR 链接

演示模式说明：
- 可在 `backend/.env` 中设置 `DEMO_MODE=true`
- 启用后后端会返回固定示例结果，适合网络不稳定或现场演示
- 任务详情页会显示明显的“演示模式”提示

演示成功标志：页面状态变为“已完成”，并展示 PR 信息、变更摘要、风险建议和 Markdown 报告下载按钮。

## 开发进度

- [x] MVP：PR 拉取 + LLM 分析 + 流式前端
- [x] 规则引擎预筛
- [x] 分析历史
- [x] 大 PR 分块并行分析
- [x] Markdown 报告导出
- [x] 七牛云对象存储报告保存（可选，配置 QINIU_* 后启用）
- [x] GitHub Webhook 自动 Review

## API 调用示例

### 1) 创建评审任务

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/reviews" \
  -H "Content-Type: application/json" \
  -d '{"pr_url":"https://github.com/octocat/Hello-World/pull/1"}'
```

### 2) 查询评审列表（分页 + 状态筛选）

```bash
curl "http://127.0.0.1:8000/api/v1/reviews?page=1&page_size=20&status=completed"
```

`status` 可选值：`pending`、`fetching`、`analyzing`、`completed`、`failed`

### 3) 订阅分析流（SSE）

```bash
curl -N "http://127.0.0.1:8000/api/v1/reviews/{task_id}/stream"
```

## 测试与质量检查

```bash
cd backend
pytest -q
```

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
