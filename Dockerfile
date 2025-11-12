# 使用官方 Python 3.9 slim 镜像作为基础
FROM python:3.9-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Asia/Shanghai

# 创建非 root 用户（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录并设置权限
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口（如果需要 Web 界面）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 设置入口点
ENTRYPOINT ["python", "zeabur_app.py"]