# Zeabur 部署指南

本文档介绍如何将 Coze 工作流执行器部署到 Zeabur 平台。

## 🚀 快速开始

### 1. 准备工作

- 注册 [Zeabur](https://zeabur.com) 账号
- 准备你的 Coze API 令牌
- 获取工作流 ID

### 2. 一键部署

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates/3WPNLC)

或者手动部署：

1. 登录 Zeabur 控制台
2. 点击 "Create New Project"
3. 选择 "Deploy from GitHub"
4. 选择你的代码仓库
5. 配置环境变量
6. 点击 Deploy

## 📋 环境变量配置

部署时需要配置以下环境变量：

| 变量名 | 描述 | 必需 | 默认值 |
|--------|------|------|--------|
| `COZE_API_TOKEN` | Coze API 令牌 | ✅ | - |
| `WORKFLOW_ID` | 工作流 ID | ✅ | `7569877408963231763` |
| `SCHEDULE_ENABLED` | 是否启用定时任务 | ❌ | `true` |
| `DAILY_TIME` | 每天执行时间 (HH:MM) | ❌ | `09:00` |
| `TIMEZONE` | 时区 | ❌ | `Asia/Shanghai` |
| `TIMEOUT_SECONDS` | 超时时间（秒） | ❌ | `1800` |
| `MAX_RETRIES` | 最大重试次数 | ❌ | `3` |
| `RETRY_DELAY_SECONDS` | 重试延迟（秒） | ❌ | `60` |
| `COZE_BASE_URL` | Coze API 基础 URL | ❌ | `https://api.coze.cn` |
| `LOG_LEVEL` | 日志级别 | ❌ | `INFO` |
| `LOG_FILE` | 日志文件路径 | ❌ | `coze_workflow.log` |
| `PORT` | HTTP 服务器端口 | ❌ | `8080` |

## 🔧 配置示例

### 基本配置
```bash
COZE_API_TOKEN=your_api_token_here
WORKFLOW_ID=7569877408963231763
```

### 高级配置
```bash
COZE_API_TOKEN=your_api_token_here
WORKFLOW_ID=7569877408963231763
SCHEDULE_ENABLED=true
DAILY_TIME=09:00
TIMEZONE=Asia/Shanghai
TIMEOUT_SECONDS=1800
MAX_RETRIES=3
LOG_LEVEL=INFO
PORT=8080
```

## 📊 监控和日志

### 健康检查
部署后可以通过以下 URL 检查应用状态：
- `https://your-app.zeabur.app/health` - 健康检查
- `https://your-app.zeabur.app/metrics` - 指标信息
- `https://your-app.zeabur.app/` - 主页

### 日志查看
在 Zeabur 控制台中可以查看实时日志，或者通过日志文件查看。

## 🔄 功能特性

### ✅ 已实现功能
- **定时任务**: 支持每天定时执行工作流
- **失败重试**: 自动重试失败的任务（最多3次）
- **超时处理**: 支持长时间运行的任务（默认1800秒超时）
- **环境变量配置**: 完全通过环境变量配置，适合云部署
- **健康检查**: 提供 HTTP 健康检查接口
- **日志记录**: 详细的日志记录，便于问题排查
- **安全最佳实践**: 使用非 root 用户运行容器

### 🎯 使用场景
- 定时执行 Coze 工作流
- 自动化任务处理
- 云端定时任务调度
- 工作流失败自动重试

## 🐳 Docker 本地测试

在本地使用 Docker 测试：

```bash
# 构建镜像
docker build -t coze-workflow-runner .

# 运行容器
docker run -d \
  -e COZE_API_TOKEN=your_token \
  -e WORKFLOW_ID=your_workflow_id \
  -p 8080:8080 \
  --name coze-runner \
  coze-workflow-runner

# 查看日志
docker logs -f coze-runner
```

## 🔍 故障排查

### 常见问题

1. **API 令牌无效**
   - 检查 `COZE_API_TOKEN` 是否正确
   - 确认令牌有执行工作流的权限

2. **工作流执行失败**
   - 检查 `WORKFLOW_ID` 是否正确
   - 查看日志了解详细错误信息

3. **定时任务不执行**
   - 检查 `SCHEDULE_ENABLED` 是否为 `true`
   - 确认 `DAILY_TIME` 格式正确（HH:MM）

### 日志分析
应用会记录详细的日志，包括：
- 应用启动信息
- 工作流执行状态
- 错误信息和堆栈跟踪
- 定时任务调度信息

## 🔒 安全建议

1. **保护 API 令牌**
   - 将 `COZE_API_TOKEN` 设置为敏感环境变量
   - 不要在代码中硬编码令牌

2. **网络配置**
   - 使用 HTTPS 访问应用
   - 配置适当的防火墙规则

3. **权限控制**
   - 使用最小权限原则
   - 定期轮换 API 令牌

## 📚 相关文档

- [Coze API 文档](https://www.coze.com/docs)
- [Zeabur 文档](https://docs.zeabur.com)
- [Docker 最佳实践](https://docs.docker.com/develop/dev-best-practices/)

## 🤝 支持

如有问题，请：
1. 查看应用日志
2. 检查环境变量配置
3. 验证 API 令牌和工作流 ID
4. 联系技术支持

## 📄 许可证

MIT License - 详见 LICENSE 文件