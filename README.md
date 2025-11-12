# Coze 工作流执行器

这是一个优化后的 Coze 工作流执行器，支持定时触发、失败重试和动态配置。

## 功能特性

- ✅ **定时任务**: 支持每天定时执行工作流
- ✅ **失败重试**: 自动重试失败的任务（最多3次）
- ✅ **超时处理**: 支持长时间运行的任务（默认1800秒超时）
- ✅ **动态配置**: 通过配置文件灵活设置参数
- ✅ **日志记录**: 详细的日志记录，便于问题排查
- ✅ **状态监控**: 支持查看运行器状态信息

## 安装依赖

```bash
pip3 install cozepy schedule pytz tenacity
```

## 配置文件

编辑 `config.json` 文件来配置你的参数：

```json
{
  "schedule": {
    "enabled": true,              // 是否启用定时任务
    "daily_time": "09:00",        // 每天执行时间
    "timezone": "Asia/Shanghai"   // 时区
  },
  "workflow": {
    "workflow_id": "7569877408963231763",  // 工作流ID
    "timeout_seconds": 1800,      // 超时时间（秒）
    "max_retries": 3,             // 最大重试次数
    "retry_delay_seconds": 60     // 重试延迟（秒）
  },
  "api": {
    "token": "your_api_token",    // API令牌
    "base_url": "https://api.coze.cn"
  },
  "logging": {
    "level": "INFO",              // 日志级别
    "file": "coze_workflow.log"   // 日志文件
  }
}
```

## 使用方法

### 1. 立即运行一次

```bash
python3 coze_optimized.py --run-once
```

### 2. 启动定时任务

```bash
python3 coze_optimized.py
```

程序将在后台运行，按照配置的时间每天执行工作流。

### 3. 查看状态

```bash
python3 coze_optimized.py --status
```

### 4. 使用自定义配置文件

```bash
python3 coze_optimized.py --config my_config.json --run-once
```

## 命令行参数

- `--config`: 指定配置文件路径（默认：config.json）
- `--run-once`: 立即运行一次工作流
- `--status`: 显示运行器状态信息

## 日志文件

所有操作都会记录到日志文件中，默认文件为 `coze_workflow.log`。

## 错误处理

- **超时处理**: 工作流执行时间超过配置的超时时间会自动重试
- **网络错误**: 网络连接问题会自动重试，最多重试3次
- **配置错误**: 配置文件格式错误会给出明确的错误提示

## 注意事项

1. 确保 API 令牌有效且有足够的权限
2. 工作流 ID 必须正确配置
3. 定时任务需要保持程序持续运行
4. 日志文件会不断增长，建议定期清理

## 故障排查

如果遇到问题，请检查：

1. 配置文件格式是否正确
2. API 令牌是否有效
3. 网络连接是否正常
4. 查看日志文件获取详细错误信息

## 更新配置

修改 `config.json` 文件后，重启程序即可生效。