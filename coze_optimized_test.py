#!/usr/bin/env python3
"""
简化测试版本 - 用于验证功能而不实际执行工作流
"""

import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

import pytz
import schedule
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from httpx import ReadTimeout


class CozeWorkflowRunnerTest:
    """测试版本的 Coze 工作流运行器"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化运行器"""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.logger.info("测试模式：Coze 工作流运行器初始化成功")
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def setup_logging(self):
        """设置日志记录"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_file = log_config.get('file', 'coze_workflow_test.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception_type((ReadTimeout, Exception))
    )
    def run_workflow_with_retry(self) -> Optional[Dict[str, Any]]:
        """模拟工作流执行，支持重试机制"""
        workflow_config = self.config['workflow']
        workflow_id = workflow_config['workflow_id']
        timeout = workflow_config.get('timeout_seconds', 1800)
        
        self.logger.info(f"开始执行工作流 {workflow_id} (测试模式)")
        
        try:
            # 模拟执行时间
            start_time = time.time()
            
            # 模拟随机失败（第一次失败，第二次成功）
            import random
            if random.random() < 0.5 and not hasattr(self, '_test_success'):
                self.logger.warning("模拟工作流执行失败，将触发重试机制")
                raise ReadTimeout("模拟超时错误")
            
            # 模拟成功
            self._test_success = True
            time.sleep(2)  # 模拟执行时间
            
            execution_time = time.time() - start_time
            self.logger.info(f"工作流执行成功，耗时: {execution_time:.2f}秒")
            
            result = {
                'workflow_id': workflow_id,
                'status': 'success',
                'execution_time': execution_time,
                'message': '测试模式执行成功',
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"工作流数据: {result}")
            return result
            
        except ReadTimeout as e:
            self.logger.error(f"工作流执行超时 ({timeout}秒): {e}")
            raise
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            raise
    
    def scheduled_job(self):
        """定时任务执行函数"""
        self.logger.info("=== 定时任务开始执行 (测试模式) ===")
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
        self.logger.info("=== 手动运行工作流 (测试模式) ===")
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
                time.sleep(10)  # 每10秒检查一次（测试模式）
        except KeyboardInterrupt:
            self.logger.info("定时任务调度器已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取运行器状态"""
        return {
            'config_loaded': bool(self.config),
            'client_initialized': True,  # 测试模式总是True
            'schedule_enabled': self.config.get('schedule', {}).get('enabled', False),
            'next_run': schedule.next_run().isoformat() if schedule.next_run() else None,
            'workflow_id': self.config.get('workflow', {}).get('workflow_id'),
            'timeout': self.config.get('workflow', {}).get('timeout_seconds', 1800),
            'max_retries': 3,
            'mode': 'test'
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Coze 工作流执行器 - 测试版本')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--run-once', action='store_true', help='立即运行一次')
    parser.add_argument('--status', action='store_true', help='显示状态信息')
    
    args = parser.parse_args()
    
    try:
        runner = CozeWorkflowRunnerTest(args.config)
        
        if args.status:
            import json
            status = runner.get_status()
            print("运行器状态 (测试模式):")
            print(json.dumps(status, indent=2, ensure_ascii=False))
            return
        
        if args.run_once:
            result = runner.run_once()
            if result:
                print("工作流执行成功 (测试模式)!")
                print(f"结果: {result}")
            else:
                print("工作流执行失败 (测试模式)!")
                exit(1)
        else:
            runner.run_scheduler()
            
    except Exception as e:
        print(f"程序启动失败: {e}")
        exit(1)


if __name__ == "__main__":
    main()