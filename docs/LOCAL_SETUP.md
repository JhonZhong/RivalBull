# 小米 MiMo 本地运行说明

本次开发使用三个 worktree：`worktrees/backend` 运行后端，`worktrees/frontend` 运行前端，`worktrees/api` 保存部署适配。根目录 `main` 维护本文档；根目录的旧 `backend/` 尚未合入此次功能修改，启动时请使用下面的路径。

## 1. 填写密钥

编辑 `D:\PROJECT\RivalBull\worktrees\backend\backend\.env`，只需填写：

```dotenv
LLM_API_KEY=
BOCHA_API_KEY=
```

- `LLM_API_KEY`：你的小米 Token Plan 专属密钥，与已配置的中国集群地址配套。
- `BOCHA_API_KEY`：博查搜索密钥，用于联网取证。没有它可以启动应用、浏览专家页面并测试模型，但不能完成正常的联网调研。
- 真实密钥只放在 `.env`；`.env.example` 是可提交的空密钥模板。`.env` 已被 Git 忽略。
- 不需要在前端填写模型或搜索密钥。

已配置的模型分工：

| 配置 | 模型 | 用途 |
|---|---|---|
| `LLM_MODEL` | `mimo-v2.6-flash` | 默认调用、模型连通性检查 |
| `LLM_MODEL_CORE` | `mimo-v2.6-pro` | 核心分析、核心报告章节 |
| `LLM_MODEL_AUX` | `mimo-v2.6-flash` | 辅助章节 |
| `LLM_MODEL_FAST` | `mimo-v2.6-flash` | 规划、专家指派等轻任务 |

地址：`https://token-plan-cn.xiaomimimo.com/v1`。

按照小米官方文档（核对日期：2026-09-26），Token Plan 暂不包含 `mimo-v2.6-pro-ultraspeed`。如果后续使用该模型，需要将地址换为 `https://api.xiaomimimo.com/v1`、填写按量付费 API 的对应密钥，再修改 `LLM_MODEL_CORE`。程序不会自动切换到付费服务。

参考：[Token Plan 与 UltraSpeed](https://mimo.mi.com/docs/zh-CN/quick-start/faq/token-plan/desktop-guide)、[OpenAI 兼容接口参数](https://mimo.mi.com/docs/zh-CN/api/chat/openai-api)。

MiMo 请求使用 `max_completion_tokens`，并明确关闭思考模式，沿用当前流水线的非思考输出策略，避免思考内容占用章节输出预算。旧的 `ZHIPU_*` 环境变量仍兼容；同一配置源中优先使用 `LLM_*`。

## 2. 一键启动（Windows）

双击项目根目录的 `start.bat`。脚本会定位 `worktrees/backend/backend` 和 `worktrees/frontend/frontend`，后台启动前后端，等待健康检查通过后自动打开 `http://127.0.0.1:3400`。

- 可以从任意工作目录启动，不需要先激活虚拟环境。
- 已运行且健康的服务会被复用，重复双击不会再启动一份。
- 端口被其他服务占用时会显示错误，不会强行结束其他进程。
- 后台日志位于项目根目录 `.run-logs/`；失败时启动窗口会保留错误信息。
- 启动检查不会调用付费模型或搜索服务。
- 命令行使用 `start.bat -NoBrowser` 可以只启动服务，不自动打开浏览器。

停止时双击根目录的 `stop.bat`。它会根据本项目虚拟环境和 Vite 脚本的完整路径识别进程，并结束前后端及其子进程；不会仅凭端口号结束其他项目。重复停止也可安全执行，数据库、密钥文件和日志均保留。正在执行的调研会被中断，尚未保存的结果可能丢失。

命令行使用 `stop.bat -NoPause` 可以在发生错误时直接返回退出码，不等待按键。需要重新启动时再次双击 `start.bat`。

下面保留手动启动方式，方便查看实时输出和调试。

### 手动启动后端（PowerShell）

```powershell
Set-Location D:\PROJECT\RivalBull\worktrees\backend\backend
.\run.ps1
```

脚本使用此目录的 `.venv`，监听 `127.0.0.1:8010`，并监视 Python 文件及 `.env` 变化。保存密钥后等待重载完成；如果没有重载，可按 Ctrl+C 后重新运行。

在新的环境中首次安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -X utf8 -m pip install -r requirements.txt
```

`-X utf8` 用于避免中文 Windows 环境下 pip 按 GBK 读取依赖文件中的 UTF-8 注释。

## 3. 启动前端（另开一个 PowerShell）

```powershell
Set-Location D:\PROJECT\RivalBull\worktrees\frontend\frontend
npm run dev
```

首次安装使用 `npm ci`。前端地址为 `http://localhost:3400`，Vite 已将 `/api` 代理到 `http://127.0.0.1:8010`。这里的前端和后端来自不同 worktree，通过 HTTP 联调。

同一端口只启动一份服务；如果本次配置会话已经启动服务，可直接访问，不要重复启动。

## 4. 验证

```powershell
# 不消耗模型额度：检查服务及密钥是否已读取
Invoke-RestMethod http://127.0.0.1:8010/health

# 会调用一次默认 Flash 模型：需先填好小米密钥
Invoke-RestMethod http://127.0.0.1:8010/api/llm/ping

# 会调用搜索服务：需先填好博查密钥
Invoke-RestMethod 'http://127.0.0.1:8010/api/search?q=MiMo&num=1'
```

`/health` 返回 `status: ok` 只表示服务运行；`llm_configured: true` 只表示密钥非空。实际模型授权、网络及额度由 `/api/llm/ping` 的 `ok` 结果验证。搜索结果也应检查 `ok` 字段。

两类密钥验证成功后，在首页选择快速模式，输入一个明确的竞品对比主题，完成澄清并观察工作台是否最终生成报告。

离线检查（不会调用真实模型）：

```powershell
Set-Location D:\PROJECT\RivalBull\worktrees\backend\backend
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v

Set-Location D:\PROJECT\RivalBull\worktrees\frontend\frontend
npm run lint
npm run build
```

## 5. 部署副本

`worktrees/api/api/.env.example` 已准备同样的模板，MiMo 适配代码位于该 worktree 的 `api/` 内。云部署时在环境变量设置中填写这些变量。先合并 backend 与 api 分支的代码，确保最终发布分支同时包含本地后端和部署副本的改动；真实 `.env` 不参与合并。
