# Zeabur 部署指南

## 🚀 快速部署

### 方法一：一键部署（推荐）
点击下面的按钮直接部署到 Zeabur：

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/deploy?template=https://github.com/your-username/coze-workflow-scheduler)

### 方法二：手动部署

## 📋 部署前准备

### 1. 获取 Coze API Token
1. 登录 [Coze 平台](https://coze.cn)
2. 进入个人设置 → API 管理
3. 创建新的 API Token
4. 复制生成的 Token

### 2. 获取工作流 ID
1. 在 Coze 平台创建或选择一个工作流
2. 从工作流 URL 中复制 ID（通常是 URL 最后的数字）

### 3. 配置定时任务（可选）
选择适合的时间格式：

| 配置格式 | 示例 | 说明 |
|----------|------|------|
| `daily:HH:MM` | `daily:18:00` | 每天18:00执行 |
| `cron:cron_expr` | `cron:0 */6 * * *` | 每6小时执行 |
| `interval:seconds` | `interval:3600` | 每1小时执行 |
| `hourly:MM` | `hourly:30` | 每小时的30分执行 |
| `weekly:day:HH:MM` | `weekly:monday:09:00` | 每周一09:00执行 |
| `monthly:day:HH:MM` | `monthly:1:18:00` | 每月1号18:00执行 |

## 🎯 部署步骤

### 步骤 1：Fork 仓库
1. 访问项目 GitHub 仓库
2. 点击右上角的 "Fork" 按钮
3. 将仓库 Fork 到你的 GitHub 账户

### 步骤 2：注册 Zeabur
1. 访问 [zeabur.com](https://zeabur.com)
2. 点击 "Sign Up" 注册账户
3. 使用 GitHub 账户授权登录

### 步骤 3：创建项目
1. 登录 Zeabur 控制台
2. 点击 "Create Project"
3. 输入项目名称（如：coze-scheduler）
4. 选择你 Fork 的 GitHub 仓库

### 步骤 4：配置环境变量

#### Docker环境变量支持
项目在Docker容器中支持以下环境变量，已在Dockerfile中完整配置：

##### 必需环境变量
| 变量名 | 说明 | 示例 |
|--------|------|------|
| `COZE_API_TOKEN` | Coze API 令牌（必需） | `cztei_xxx...` |
| `COZE_WORKFLOW_ID` | 工作流 ID（必需） | `756925844681878738` |

##### 可选环境变量
| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `COZE_API_BASE` | API 基础地址 | `https://api.coze.cn` | `https://api.coze.cn` |
| `SCHEDULE_CONFIG` | 定时配置 | `daily:18:00` | `daily:14:30` |
| `SCHEDULE_TIMEZONE` | 时区设置 | `UTC` | `Asia/Shanghai` |
| `MAX_RETRIES` | 最大重试次数 | `5` | `3` |
| `RETRY_DELAY` | 重试间隔（秒） | `60` | `30` |

#### Zeabur部署配置
在 Zeabur 控制台中，进入项目设置，添加环境变量：

**生产环境配置示例：**
```bash
COZE_API_TOKEN=your_api_token_here
COZE_WORKFLOW_ID=756925844681878738
SCHEDULE_CONFIG=daily:18:00
SCHEDULE_TIMEZONE=UTC
MAX_RETRIES=5
RETRY_DELAY=60
```

**开发环境配置示例：**
```bash
COZE_API_TOKEN=your_api_token_here
COZE_WORKFLOW_ID=756925844681878738
SCHEDULE_CONFIG=interval:300  # 每5分钟测试
SCHEDULE_TIMEZONE=UTC
MAX_RETRIES=3
RETRY_DELAY=30
```

#### 定时配置示例
```bash
# 每天14:30执行
SCHEDULE_CONFIG="daily:14:30"

# 每6小时执行一次
SCHEDULE_CONFIG="interval:21600"

# 每周一上午9点执行
SCHEDULE_CONFIG="weekly:monday:09:00"

# 每月1号和15号执行
# 需要设置两次，或修改代码支持多日期
SCHEDULE_CONFIG="monthly:1:09:00"
```

### 步骤 5：部署
1. Zeabur 会自动检测 Dockerfile
2. 点击 "Deploy" 开始部署
3. 等待构建完成（通常需要 2-5 分钟）

## 📊 验证部署

### 查看日志
1. 在 Zeabur 控制台中点击你的项目
2. 进入 "Logs" 标签页
3. 查看实时日志输出

### 预期日志
```
Starting workflow scheduler...
Workflow will run daily at 18:00
Running workflow once for testing...
Attempting to run workflow (attempt 1/5)
```

## ⚙️ 配置说明

### 定时任务
- 默认每天 18:00 UTC 执行（北京时间 02:00）
- 如需修改时间，请编辑 `wewerss.py` 中的 `schedule.every().day.at("18:00")`

### 重试机制
- 失败后 60 秒自动重试
- 最多重试 5 次
- 可在代码中修改 `max_retries` 和 `retry_delay` 参数

## 🔍 故障排除

### 部署失败
1. 检查 Dockerfile 是否正确
2. 确认环境变量配置完整
3. 查看构建日志获取详细错误信息

### 认证失败
1. 确认 `COZE_API_TOKEN` 正确无误
2. 检查 Token 是否过期
3. 验证工作流 ID 是否正确

### 时区问题
- 应用使用 UTC 时间
- 18:00 UTC = 北京时间 02:00（次日）
- 如需调整，请修改代码中的时间设置

## 📈 监控和维护

### 查看运行状态
- 在 Zeabur 控制台查看项目状态
- 监控资源使用情况
- 查看历史日志

### 更新应用
1. 在 GitHub 中更新你的 Fork
2. Zeabur 会自动检测变更并重新部署
3. 或手动触发重新部署

### 停止服务
- 在 Zeabur 控制台中暂停项目
- 或删除项目以完全停止

## 💡 最佳实践

1. **安全**：不要在代码中硬编码敏感信息
2. **监控**：定期检查日志确保正常运行
3. **备份**：保存重要的配置信息
4. **更新**：及时更新依赖和代码

## 🆘 获取帮助

- Zeabur 官方文档：[docs.zeabur.com](https://docs.zeabur.com)
- Coze 官方文档：[www.coze.cn/docs](https://www.coze.cn/docs)
- 提交 Issue：在 GitHub 仓库提交问题

## 📚 相关链接

- [Zeabur 官网](https://zeabur.com)
- [Coze 平台](https://coze.cn)
- [项目仓库](https://github.com/your-username/coze-workflow-scheduler)