#!/usr/bin/env python3
"""
Zeabur 部署版本的 Coze 工作流执行器
支持环境变量配置，适合云原生部署
"""

import json
import logging
import time
import traceback
import os
from datetime import datetime
from typing import Dict, Any, Optional

import pytz
import schedule
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL
from httpx import ReadTimeout


class ZeaburCozeWorkflowRunner:
    """适配 Zeabur 的 Coze 工作流运行器"""
    
    def __init__(self):
        """初始化运行器 - 从环境变量读取配置"""
        self.config = self.load_config_from_env()
        self.setup_logging()
        self.coze_client = None
        self.init_coze_client()
        
    def load_config_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {
            'schedule': {
                'enabled': os.getenv('SCHEDULE_ENABLED', 'true').lower() == 'true',
                'daily_time': os.getenv('DAILY_TIME', '09:00'),
                'timezone': os.getenv('TIMEZONE', 'Asia/Shanghai')
            },
            'workflow': {
                'workflow_id': os.getenv('WORKFLOW_ID', '7569877408963231763'),
                'timeout_seconds': int(os.getenv('TIMEOUT_SECONDS', '1800')),
                'max_retries': int(os.getenv('MAX_RETRIES', '3')),
                'retry_delay_seconds': int(os.getenv('RETRY_DELAY_SECONDS', '60'))
            },
            'api': {
                'token': os.getenv('COZE_API_TOKEN', ''),
                'base_url': os.getenv('COZE_BASE_URL', COZE_CN_BASE_URL)
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'file': os.getenv('LOG_FILE', 'coze_workflow.log')
            },
            'zeabur': {
                'port': int(os.getenv('PORT', '8080')),
                'health_check_path': os.getenv('HEALTH_CHECK_PATH', '/health'),
                'metrics_path': os.getenv('METRICS_PATH', '/metrics')
            }
        }
        
        # 验证必需的配置
        if not config['api']['token']:
            raise ValueError("COZE_API_TOKEN 环境变量必须设置")
        
        if not config['workflow']['workflow_id']:
            raise ValueError("WORKFLOW_ID 环境变量必须设置")
            
        return config
    
    def setup_logging(self):
        """设置日志记录"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_file = log_config.get('file', 'coze_workflow.log')
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Zeabur Coze 工作流运行器初始化成功")
    
    def init_coze_client(self):
        """初始化 Coze 客户端"""
        try:
            api_config = self.config['api']
            self.coze_client = Coze(
                auth=TokenAuth(token=api_config['token']),
                base_url=api_config.get('base_url', COZE_CN_BASE_URL)
            )
            self.logger.info("Coze 客户端初始化成功")
        except Exception as e:
            self.logger.error(f"Coze 客户端初始化失败: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ReadTimeout, Exception))
    )
    def run_workflow_with_retry(self) -> Optional[Dict[str, Any]]:
        """运行工作流，支持重试机制"""
        workflow_config = self.config['workflow']
        workflow_id = workflow_config['workflow_id']
        timeout = workflow_config.get('timeout_seconds', 1800)
        
        self.logger.info(f"开始执行工作流 {workflow_id}")
        
        try:
            start_time = time.time()
            
            # 创建工作流运行
            workflow = self.coze_client.workflows.runs.create(
                workflow_id=workflow_id,
            )
            
            execution_time = time.time() - start_time
            self.logger.info(f"工作流执行成功，耗时: {execution_time:.2f}秒")
            self.logger.info(f"工作流数据: {workflow.data}")
            
            return workflow.data
            
        except ReadTimeout as e:
            self.logger.error(f"工作流执行超时 ({timeout}秒): {e}")
            raise
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            raise
    
    def scheduled_job(self):
        """定时任务执行函数"""
        self.logger.info("=== 定时任务开始执行 ===")
        try:
            result = self.run_workflow_with_retry()
            self.logger.info("=== 定时任务执行成功 ===")
            return result
        except Exception as e:
            self.logger.error(f"=== 定时任务执行失败 ===")
            self.logger.error(f"错误: {e}")
            return None
    
    def run_once(self):
        """立即运行一次工作流"""
        self.logger.info("=== 手动运行工作流 ===")
        return self.scheduled_job()
    
    def setup_schedule(self):
        """设置定时任务"""
        schedule_config = self.config['schedule']
        
        if not schedule_config.get('enabled', False):
            self.logger.info("定时任务已禁用")
            return
        
        daily_time = schedule_config['daily_time']
        timezone = schedule_config.get('timezone', 'Asia/Shanghai')
        
        # 设置时区
        tz = pytz.timezone(timezone)
        
        # 添加定时任务
        schedule.every().day.at(daily_time).do(self.scheduled_job)
        
        self.logger.info(f"定时任务已设置: 每天 {daily_time} ({timezone})")
        
        # 显示下次运行时间
        next_run = schedule.next_run()
        if next_run:
            local_next_run = next_run.astimezone(tz)
            self.logger.info(f"下次运行时间: {local_next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查接口"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'config_loaded': bool(self.config),
            'client_initialized': bool(self.coze_client),
            'schedule_enabled': self.config.get('schedule', {}).get('enabled', False),
            'workflow_id': self.config.get('workflow', {}).get('workflow_id'),
            'timeout': self.config.get('workflow', {}).get('timeout_seconds', 1800),
            'max_retries': 3
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标信息"""
        return {
            'app': 'coze-workflow-runner',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'config': {
                'schedule_enabled': self.config.get('schedule', {}).get('enabled', False),
                'workflow_id': self.config.get('workflow', {}).get('workflow_id'),
                'timezone': self.config.get('schedule', {}).get('timezone', 'Asia/Shanghai')
            }
        }
    
    def run_scheduler(self):
        """运行定时任务调度器"""
        self.setup_schedule()
        
        if not self.config['schedule'].get('enabled', False):
            self.logger.info("定时任务已禁用，程序将退出")
            return
        
        self.logger.info("定时任务调度器已启动，按 Ctrl+C 停止")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("定时任务调度器已停止")


# 简单的 HTTP 服务器（用于健康检查和指标）
class SimpleHTTPServer:
    """简单的 HTTP 服务器，用于健康检查和指标"""
    
    def __init__(self, runner: ZeaburCozeWorkflowRunner, port: int = 8080):
        self.runner = runner
        self.port = port
        self.logger = logging.getLogger(__name__)
    
    def start_server(self):
        """启动 HTTP 服务器"""
        import http.server
        import socketserver
        import json
        
        class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    health_data = self.server.runner.health_check()
                    self.wfile.write(json.dumps(health_data).encode())
                
                elif self.path == '/metrics':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    metrics_data = self.server.runner.get_metrics()
                    self.wfile.write(json.dumps(metrics_data).encode())
                
                elif self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html = """
                    <html>
                    <head><title>Coze Workflow Runner</title></head>
                    <body>
                        <h1>Coze Workflow Runner</h1>
                        <p>Status: Running</p>
                        <ul>
                            <li><a href="/health">Health Check</a></li>
                            <li><a href="/metrics">Metrics</a></li>
                        </ul>
                    </body>
                    </html>
                    """
                    self.wfile.write(html.encode())
                
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # 自定义日志格式
                self.server.runner.logger.info(f"HTTP: {format % args}")
        
        # 创建服务器
        with socketserver.TCPServer(("", self.port), HealthCheckHandler) as httpd:
            httpd.runner = self.runner
            self.logger.info(f"HTTP 服务器启动在端口 {self.port}")
            self.logger.info(f"访问 http://localhost:{self.port}/health 查看健康状态")
            self.logger.info(f"访问 http://localhost:{self.port}/metrics 查看指标")
            
            # 在非阻塞模式下运行
            httpd.serve_forever()


def main():
    """主函数 - Zeabur 版本"""
    import argparse
    import threading
    
    parser = argparse.ArgumentParser(description='Zeabur Coze 工作流执行器')
    parser.add_argument('--run-once', action='store_true', help='立即运行一次')
    parser.add_argument('--no-schedule', action='store_true', help='禁用定时任务')
    parser.add_argument('--no-http', action='store_true', help='禁用 HTTP 服务器')
    
    args = parser.parse_args()
    
    try:
        runner = ZeaburCozeWorkflowRunner()
        
        # 如果禁用定时任务，修改配置
        if args.no_schedule:
            runner.config['schedule']['enabled'] = False
        
        # 启动 HTTP 服务器（除非显式禁用）
        if not args.no_http:
            http_port = runner.config['zeabur']['port']
            http_server = SimpleHTTPServer(runner, http_port)
            
            # 在单独的线程中启动 HTTP 服务器
            http_thread = threading.Thread(target=http_server.start_server, daemon=True)
            http_thread.start()
        
        if args.run_once:
            result = runner.run_once()
            if result:
                print("工作流执行成功!")
            else:
                print("工作流执行失败!")
                exit(1)
        else:
            runner.run_scheduler()
            
    except Exception as e:
        print(f"程序启动失败: {e}")
        exit(1)


if __name__ == "__main__":
    main()