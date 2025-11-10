# Zeabur Project.yaml 使用指南

## 📋 项目概述

您已经创建了完整的 `project.yaml` 文件，这是 Zeabur 平台的部署模板配置文件。该文件定义了：

- ✅ **服务配置**：Python 应用的完整部署规范
- ✅ **环境变量**：所有支持的环境变量及其默认值
- ✅ **资源限制**：内存和 CPU 使用限制
- ✅ **健康检查**：应用状态监控
- ✅ **部署示例**：生产/开发/测试环境配置

## 🎯 配置文件结构

### 1. 基本信息
```yaml
name: coze-workflow-scheduler
displayName: "Coze Workflow Scheduler"
description: "🤖 Automated Coze workflow scheduler with dynamic timing configuration and retry mechanism"
icon: "🤖"
```

### 2. 服务定义
```yaml
services:
  - name: app
    template: PREBUILT_V2
    spec:
      source:
        source: GITHUB
        repo: wanghengbing1/coze-workflow-scheduler  # 需要替换为您的仓库
        branch: main
```

### 3. 环境变量配置
```yaml
env:
  COZE_API_TOKEN:
    default: ""
    expose: false
    description: "Coze API token for authentication"
  
  SCHEDULE_CONFIG:
    default: "daily:18:00"
    description: "Schedule configuration (daily:HH:MM, cron:*, interval:seconds, etc.)"
```

## 🚀 使用方法

### 步骤1：更新仓库地址
在 `project.yaml` 中找到以下部分：
```yaml
repo: wanghengbing1/coze-workflow-scheduler  # 替换为您的GitHub仓库
```
将其替换为您的实际GitHub仓库地址。

### 步骤2：配置环境变量
根据您的需求修改环境变量：

#### 必需环境变量
- `COZE_API_TOKEN`: 您的Coze API令牌
- `COZE_WORKFLOW_ID`: 您的工作流ID

#### 可选环境变量（带智能默认值）
- `SCHEDULE_CONFIG`: 定时配置（默认：`daily:18:00`）
- `MAX_RETRIES`: 最大重试次数（默认：`5`）
- `RETRY_DELAY`: 重试间隔（默认：`60`秒）

### 步骤3：选择部署环境
配置文件提供了三种环境示例：

#### 生产环境（默认）
```yaml
SCHEDULE_CONFIG: "daily:18:00"
MAX_RETRIES: "5"
RETRY_DELAY: "60"
```

#### 开发环境
```yaml
SCHEDULE_CONFIG: "interval:300"  # 每5分钟
MAX_RETRIES: "3"
RETRY_DELAY: "30"
```

#### 测试环境
```yaml
SCHEDULE_CONFIG: "hourly:00"  # 每小时
MAX_RETRIES: "2"
RETRY_DELAY: "10"
```

## 📊 支持的定时格式

| 格式 | 示例 | 说明 |
|------|------|------|
| `daily:HH:MM` | `daily:18:00` | 每天18:00执行 |
| `cron:cron_expr` | `cron:0 */6 * * *` | 每6小时执行 |
| `interval:seconds` | `interval:3600` | 每1小时执行 |
| `hourly:MM` | `hourly:30` | 每小时的30分执行 |
| `weekly:day:HH:MM` | `weekly:monday:18:00` | 每周一18:00执行 |
| `monthly:day:HH:MM` | `monthly:1:18:00` | 每月1号18:00执行 |

## 🔧 资源配置

### 内存和CPU限制
```yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

### 健康检查
```yaml
healthCheck:
  enabled: true
  path: "/health"
  interval: 30
  timeout: 10
  retries: 3
```

## 🎯 一键部署

### 使用Zeabur CLI
```bash
# 安装Zeabur CLI
npm install -g @zeabur/cli

# 部署项目
zeabur deploy --template project.yaml
```

### 使用Zeabur网页界面
1. 访问 [zeabur.com](https://zeabur.com)
2. 点击 "Create Project"
3. 选择 "Import from GitHub"
4. 上传您的 `project.yaml` 文件
5. 配置环境变量
6. 点击部署

## 📋 环境变量详解

### Coze API配置
- **COZE_API_TOKEN**: 您的Coze API令牌（必需）
- **COZE_WORKFLOW_ID**: 工作流ID（必需）
- **COZE_API_BASE**: API基础地址（默认：https://api.coze.cn）

### 定时配置
- **SCHEDULE_CONFIG**: 定时配置格式
- **SCHEDULE_TIMEZONE**: 时区设置（默认：UTC）

### 重试配置
- **MAX_RETRIES**: 最大重试次数（默认：5）
- **RETRY_DELAY**: 重试间隔秒数（默认：60）

### Python配置
- **PYTHONUNBUFFERED**: Python输出缓冲（默认：1）
- **PORT**: 应用端口（默认：8080）

## 🆘 常见问题

### Q1: 部署失败怎么办？
1. 检查GitHub仓库是否公开
2. 验证环境变量是否正确
3. 查看Zeabur控制台日志
4. 确认Dockerfile是否正确

### Q2: 如何修改定时配置？
在Zeabur控制台中修改 `SCHEDULE_CONFIG` 环境变量即可。

### Q3: 资源不足怎么办？
可以调整 `resources` 部分的内存和CPU限制。

### Q4: 如何查看日志？
在Zeabur控制台中进入项目的 "Logs" 标签页。

## 📞 获取帮助

- **Zeabur文档**: [docs.zeabur.com](https://docs.zeabur.com)
- **项目仓库**: [GitHub Issues](https://github.com/wanghengbing1/coze-workflow-scheduler/issues)
- **配置文件**: [project.yaml](project.yaml)

## 🎉 恭喜！

您现在拥有了完整的Zeabur部署配置！只需：

1. ✅ 更新仓库地址
2. ✅ 配置环境变量
3. ✅ 一键部署到Zeabur

您的自动化Coze工作流调度器即将上线！🚀

**下一步**: 使用Zeabur CLI或网页界面部署您的项目！
