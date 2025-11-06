# 使用官方 Python 运行时作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY wewerss.py .

# 创建日志目录
RUN mkdir -p /app/logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV COZE_API_BASE=https://api.coze.cn
ENV COZE_API_TOKEN=""
ENV COZE_WORKFLOW_ID=756925844681878738
ENV SCHEDULE_CONFIG=daily:18:00
ENV SCHEDULE_TIMEZONE=UTC
ENV MAX_RETRIES=5
ENV RETRY_DELAY=60

# 暴露端口（如果需要）
EXPOSE 8080

# 运行应用
CMD ["python", "wewerss.py"]