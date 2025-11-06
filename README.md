# Coze Workflow Scheduler

🤖 自动化 Coze 工作流调度器，支持定时执行和错误重试机制

## 功能特点

- ⏰ **定时执行**: 每天 18:00 自动运行工作流
- 🔄 **错误重试**: 失败后自动重试，最多 5 次
- 📝 **日志记录**: 完整的执行日志记录
- 🔧 **环境配置**: 支持环境变量配置
- 🐳 **容器化**: Docker 支持，易于部署

## 环境变量

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `COZE_API_TOKEN` | Coze API 令牌 | ✅ | 无 |
| `COZE_WORKFLOW_ID` | 工作流 ID | ✅ | `7569258446818755555` |
| `COZE_API_BASE` | API 基础地址 | ❌ | `https://api.coze.cn` |
| `SCHEDULE_CONFIG` | 定时配置（支持多种格式） | ❌ | `daily:18:00` |
| `SCHEDULE_TIMEZONE` | 时区设置 | ❌ | `UTC` |
| `MAX_RETRIES` | 最大重试次数 | ❌ | `5` |
| `RETRY_DELAY` | 重试间隔（秒） | ❌ | `60` |

## 定时配置说明

`SCHEDULE_CONFIG` 支持多种时间格式：

### 1. 每日定时（daily）
格式：`daily:HH:MM`
- 示例：`daily:18:00` - 每天18:00执行
- 示例：`daily:09:30` - 每天09:30执行

### 2. Cron表达式（cron）
格式：`cron:cron_expression`
- 示例：`cron:0 18 * * *` - 每天18:00执行
- 示例：`cron:0 */6 * * *` - 每6小时执行
- 示例：`cron:0 0 * * 1` - 每周一00:00执行

### 3. 间隔执行（interval）
格式：`interval:seconds`
- 示例：`interval:3600` - 每1小时执行
- 示例：`interval:7200` - 每2小时执行
- 最小间隔：60秒

### 4. 每小时（hourly）
格式：`hourly:MM`
- 示例：`hourly:00` - 每小时的00分执行
- 示例：`hourly:30` - 每小时的30分执行

### 5. 每周（weekly）
格式：`weekly:day:HH:MM`
- 示例：`weekly:monday:18:00` - 每周一18:00执行
- 示例：`weekly:friday:09:00` - 每周五09:00执行

### 6. 每月（monthly）
格式：`monthly:day:HH:MM`
- 示例：`monthly:1:18:00` - 每月1号18:00执行
- 示例：`monthly:15:09:00` - 每月15号09:00执行

## 本地运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 设置环境变量
```bash
export COZE_API_TOKEN="your_api_token_here"
export COZE_WORKFLOW_ID="your_workflow_id"
```

### 3. 运行应用
```bash
python wewerss.py
```

## Docker 部署

### 1. 构建镜像
```bash
docker build -t coze-workflow-scheduler .
```

### 2. 运行容器
```bash
docker run -d \
  -e COZE_API_TOKEN="your_api_token_here" \
  -e COZE_WORKFLOW_ID="your_workflow_id" \
  --name coze-scheduler \
  coze-workflow-scheduler
```

## Zeabur 部署

### 一键部署
[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates?template=https://github.com/your-repo/coze-workflow-scheduler)

### 手动部署步骤

1. **Fork 本仓库** 到你的 GitHub 账户

2. **登录 Zeabur**
   - 访问 [zeabur.com](https://zeabur.com)
   - 使用 GitHub 账户登录

3. **创建新项目**
   - 点击 "Create Project"
   - 选择你的 GitHub 仓库

4. **配置环境变量**
   - 在 Zeabur 控制台中，进入项目设置
   - 添加以下环境变量：
     - `COZE_API_TOKEN`: 你的 Coze API 令牌
     - `COZE_WORKFLOW_ID`: 你的工作流 ID
     - `COZE_API_BASE`: API 基础地址（可选）

5. **部署**
   - Zeabur 会自动检测 Dockerfile 并构建应用
   - 构建完成后，应用会自动运行

## 日志查看

应用会生成详细的日志文件，你可以通过以下方式查看：

### 本地日志
```bash
tail -f workflow_scheduler.log
```

### Docker 日志
```bash
docker logs coze-scheduler
```

### Zeabur 日志
在 Zeabur 控制台中查看实时日志

## 注意事项

1. **API 令牌**: 确保你的 Coze API 令牌有效
2. **工作流 ID**: 确认工作流 ID 正确无误
3. **时区**: 应用使用 UTC 时间，18:00 UTC 对应北京时间 02:00（次日）
4. **重试机制**: 失败后会在 60 秒后重试，最多 5 次

## 故障排除

### 认证失败
- 检查 `COZE_API_TOKEN` 是否正确
- 确认 API 令牌未过期

### 工作流未找到
- 检查 `COZE_WORKFLOW_ID` 是否正确
- 确认工作流在 Coze 平台存在

### 部署失败
- 检查 Dockerfile 是否正确
- 确认环境变量配置完整

## 支持

如有问题，请在 GitHub Issues 中提交问题。