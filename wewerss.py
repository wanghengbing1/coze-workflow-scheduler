"""
This example describes how to use the workflow interface to chat with dynamic scheduling and retry mechanisms.
"""

import os
import time
import datetime
import logging
import signal
import threading
import re
from typing import Optional, Dict, Any
import schedule
from croniter import croniter
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL, CozeAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables for graceful shutdown
shutdown_event = threading.Event()
request_lock = threading.Lock()
active_requests = 0

# Get configuration from environment variables
coze_api_token = os.getenv('COZE_API_TOKEN', '')
coze_api_base = os.getenv('COZE_API_BASE', 'https://api.coze.cn')
workflow_id = os.getenv('COZE_WORKFLOW_ID', '756925844681878738')

# Dynamic scheduling configuration
SCHEDULE_CONFIG = os.getenv('SCHEDULE_CONFIG', 'daily:18:00')  # 默认每天18:00
SCHEDULE_TIMEZONE = os.getenv('SCHEDULE_TIMEZONE', 'CTS')  # 默认CTS时区
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '5'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '60'))

# API request configuration
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))  # 请求超时时间（秒）
REQUEST_RETRY_BACKOFF = float(os.getenv('REQUEST_RETRY_BACKOFF', '2.0'))  # 退避乘数
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '3'))  # 最大并发请求数

# Validate required environment variables (skip in test mode)
if not coze_api_token and os.getenv('TEST_MODE', 'false').lower() != 'true':
    logger.error("COZE_API_TOKEN environment variable is required")
    exit(1)

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def is_shutdown_requested():
    """Check if shutdown has been requested."""
    return shutdown_event.is_set()

def wait_for_request_slot(timeout=30):
    """Wait for available request slot with timeout."""
    start_time = time.time()
    while active_requests >= MAX_CONCURRENT_REQUESTS:
        if is_shutdown_requested() or (time.time() - start_time) > timeout:
            return False
        time.sleep(0.1)
    return True

# Init the Coze client through the access_token (delay in test mode)
def init_coze_client():
    """Initialize Coze client with proper error handling."""
    global coze
    try:
        if not coze_api_token and os.getenv('TEST_MODE', 'false').lower() == 'true':
            # In test mode, create a mock client or skip initialization
            logger.info("Test mode detected, skipping Coze client initialization")
            return None
        
        coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)
        return coze
    except Exception as e:
        logger.error(f"Failed to initialize Coze client: {e}")
        if os.getenv('TEST_MODE', 'false').lower() == 'true':
            return None
        else:
            raise

# Initialize client
coze = init_coze_client()

def parse_schedule_config(config: str) -> Dict[str, Any]:
    """
    Parse schedule configuration string with intelligent format fixing.
    
    Supported formats:
    - daily:HH:MM (e.g., daily:18:00)
    - cron:cron_expression (e.g., cron:0 18 * * *)
    - interval:seconds (e.g., interval:3600)
    - hourly:MM (e.g., hourly:30 - 每小时的30分)
    - weekly:day:HH:MM (e.g., weekly:monday:18:00)
    - monthly:day:HH:MM (e.g., monthly:15:18:00)
    
    Returns:
        Dict containing schedule type and parameters
    """
    try:
        # 预处理配置字符串
        config = config.strip()
        
        # 使用正则表达式进行智能格式识别和修复
        patterns = {
            'daily': [
                r'^daily:(\d{1,2}):(\d{2})$',  # daily:HH:MM
                r'^daily(\d{1,2}):(\d{2})$',   # dailyHH:MM (修复格式)
            ],
            'hourly': [
                r'^hourly:(\d{1,2})$',         # hourly:MM
            ],
            'interval': [
                r'^interval:(\d+)$',           # interval:seconds
            ],
            'cron': [
                r'^cron:(.+)$',                 # cron:expression
            ],
            'weekly': [
                r'^weekly:([a-zA-Z]+):(\d{1,2}):(\d{2})$',  # weekly:day:HH:MM
            ],
            'monthly': [
                r'^monthly:(\d{1,2}):(\d{1,2}):(\d{2})$',   # monthly:day:HH:MM
            ]
        }
        
        # 尝试匹配和修复格式
        for schedule_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.match(pattern, config, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if schedule_type == 'daily':
                        if len(groups) == 2:  # daily:HH:MM 或 dailyHH:MM
                            hour, minute = groups
                            if int(hour) <= 23 and int(minute) <= 59:
                                return {
                                    'type': 'daily',
                                    'time': f"{hour}:{minute}"
                                }
                    
                    elif schedule_type == 'hourly':
                        minute = groups[0]
                        if int(minute) <= 59:
                            return {
                                'type': 'hourly',
                                'minute': int(minute)
                            }
                    
                    elif schedule_type == 'interval':
                        seconds = int(groups[0])
                        if seconds >= 60:
                            return {
                                'type': 'interval',
                                'seconds': seconds
                            }
                    
                    elif schedule_type == 'cron':
                        cron_expr = groups[0].strip()
                        if croniter.is_valid(cron_expr):
                            return {
                                'type': 'cron',
                                'expression': cron_expr
                            }
                    
                    elif schedule_type == 'weekly':
                        day, hour, minute = groups
                        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        if day.lower() in days and int(hour) <= 23 and int(minute) <= 59:
                            return {
                                'type': 'weekly',
                                'day': day.lower(),
                                'time': f"{hour}:{minute}"
                            }
                    
                    elif schedule_type == 'monthly':
                        day, hour, minute = groups
                        if 1 <= int(day) <= 31 and int(hour) <= 23 and int(minute) <= 59:
                            return {
                                'type': 'monthly',
                                'day': int(day),
                                'time': f"{hour}:{minute}"
                            }
        
        # 如果所有模式都不匹配，记录错误并返回默认值
        logger.error(f"Failed to parse schedule config '{config}': Invalid format")
        logger.info("Using default daily:18:00 schedule")
        return {
            'type': 'daily',
            'time': '18:00'
        }
        
    except Exception as e:
        logger.error(f"Failed to parse schedule config '{config}': {e}")
        logger.info("Using default daily:18:00 schedule")
        return {
            'type': 'daily',
            'time': '18:00'
        }
        
        if schedule_type == 'daily':
            # daily:HH:MM
            if len(parts) != 3:
                raise ValueError("Daily format: daily:HH:MM")
            return {
                'type': 'daily',
                'time': f"{parts[1]}:{parts[2]}"
            }
            
        elif schedule_type == 'cron':
            # cron:cron_expression
            if len(parts) < 2:
                raise ValueError("Cron format: cron:cron_expression")
            cron_expr = ':'.join(parts[1:])
            if not croniter.is_valid(cron_expr):
                raise ValueError(f"Invalid cron expression: {cron_expr}")
            return {
                'type': 'cron',
                'expression': cron_expr
            }
            
        elif schedule_type == 'interval':
            # interval:seconds
            if len(parts) != 2:
                raise ValueError("Interval format: interval:seconds")
            seconds = int(parts[1])
            if seconds < 60:
                raise ValueError("Interval must be at least 60 seconds")
            return {
                'type': 'interval',
                'seconds': seconds
            }
            
        elif schedule_type == 'hourly':
            # hourly:MM
            if len(parts) != 2:
                raise ValueError("Hourly format: hourly:MM")
            minute = int(parts[1])
            if not 0 <= minute <= 59:
                raise ValueError("Minute must be between 0-59")
            return {
                'type': 'hourly',
                'minute': minute
            }
            
        elif schedule_type == 'weekly':
            # weekly:day:HH:MM
            if len(parts) != 4:
                raise ValueError("Weekly format: weekly:day:HH:MM")
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day = parts[1].lower()
            if day not in days:
                raise ValueError(f"Day must be one of: {', '.join(days)}")
            return {
                'type': 'weekly',
                'day': day,
                'time': f"{parts[2]}:{parts[3]}"
            }
            
        elif schedule_type == 'monthly':
            # monthly:day:HH:MM
            if len(parts) != 4:
                raise ValueError("Monthly format: monthly:day:HH:MM")
            day = int(parts[1])
            if not 1 <= day <= 31:
                raise ValueError("Day must be between 1-31")
            return {
                'type': 'monthly',
                'day': day,
                'time': f"{parts[2]}:{parts[3]}"
            }
            
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
            
    except Exception as e:
        logger.error(f"Failed to parse schedule config '{config}': {e}")
        logger.info("Using default daily:18:00 schedule")
        return {
            'type': 'daily',
            'time': '18:00'
        }

def setup_schedule(schedule_config: Dict[str, Any]) -> None:
    """
    Setup schedule based on configuration.
    """
    schedule_type = schedule_config['type']
    
    if schedule_type == 'daily':
        time_str = schedule_config['time']
        schedule.every().day.at(time_str).do(scheduled_workflow_job)
        logger.info(f"Scheduled daily execution at {time_str}")
        
    elif schedule_type == 'cron':
        cron_expr = schedule_config['expression']
        # For cron expressions, we'll use a simple approach
        # In production, you might want to use a more robust cron library
        logger.info(f"Using cron expression: {cron_expr}")
        # Convert common cron patterns to schedule format
        if cron_expr == "0 18 * * *":
            schedule.every().day.at("18:00").do(scheduled_workflow_job)
        elif cron_expr == "0 0 * * *":
            schedule.every().day.at("00:00").do(scheduled_workflow_job)
        elif cron_expr == "0 */6 * * *":
            schedule.every(6).hours.do(scheduled_workflow_job)
        elif cron_expr == "0 */12 * * *":
            schedule.every(12).hours.do(scheduled_workflow_job)
        else:
            # Default to daily if can't parse
            schedule.every().day.at("18:00").do(scheduled_workflow_job)
            logger.warning(f"Cannot parse cron '{cron_expr}', using daily:18:00")
            
    elif schedule_type == 'interval':
        seconds = schedule_config['seconds']
        schedule.every(seconds).seconds.do(scheduled_workflow_job)
        logger.info(f"Scheduled interval execution every {seconds} seconds")
        
    elif schedule_type == 'hourly':
        minute = schedule_config['minute']
        schedule.every().hour.at(f":{minute:02d}").do(scheduled_workflow_job)
        logger.info(f"Scheduled hourly execution at :{minute:02d}")
        
    elif schedule_type == 'weekly':
        day = schedule_config['day']
        time_str = schedule_config['time']
        day_map = {
            'monday': schedule.every().monday,
            'tuesday': schedule.every().tuesday,
            'wednesday': schedule.every().wednesday,
            'thursday': schedule.every().thursday,
            'friday': schedule.every().friday,
            'saturday': schedule.every().saturday,
            'sunday': schedule.every().sunday
        }
        day_map[day].at(time_str).do(scheduled_workflow_job)
        logger.info(f"Scheduled weekly execution on {day} at {time_str}")
        
    elif schedule_type == 'monthly':
        # For monthly, we'll use a workaround with daily checking
        day = schedule_config['day']
        time_str = schedule_config['time']
        logger.info(f"Scheduled monthly execution on day {day} at {time_str}")
        # This will be handled specially in the scheduler loop

def run_workflow_with_retry(max_retries: int = MAX_RETRIES, retry_delay: int = RETRY_DELAY) -> Optional[dict]:
    """
    Run the workflow with retry mechanism and interruption support.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retry attempts
        
    Returns:
        Workflow result data if successful, None if all retries failed
    """
    global active_requests
    
    # Check for shutdown request before starting
    if is_shutdown_requested():
        logger.warning("Shutdown requested, skipping workflow execution")
        return None
    
    # Wait for available request slot
    if not wait_for_request_slot():
        logger.error("Timeout waiting for request slot or shutdown requested")
        return None
    
    with request_lock:
        if active_requests >= MAX_CONCURRENT_REQUESTS:
            logger.error("Max concurrent requests reached")
            return None
        active_requests += 1
    
    try:
        for attempt in range(max_retries):
            # Check for shutdown request before each attempt
            if is_shutdown_requested():
                logger.warning("Shutdown requested, stopping retry attempts")
                return None
            
            try:
                logger.info(f"Attempting to run workflow (attempt {attempt + 1}/{max_retries})")
                
                # Check if client is available (test mode)
                if coze is None:
                    if os.getenv('TEST_MODE', 'false').lower() == 'true':
                        logger.info("Test mode: simulating successful workflow execution")
                        return {"test": "success", "data": "mock_workflow_data"}
                    else:
                        raise RuntimeError("Coze client not initialized")
                
                # Create workflow run with application-level timeout control
                import concurrent.futures
                
                def create_workflow_with_timeout():
                    return coze.workflows.runs.create(workflow_id=workflow_id)
                
                # Use ThreadPoolExecutor for timeout control
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(create_workflow_with_timeout)
                    try:
                        workflow = future.result(timeout=REQUEST_TIMEOUT)
                    except concurrent.futures.TimeoutError:
                        logger.error(f"Workflow creation timed out after {REQUEST_TIMEOUT} seconds")
                        raise TimeoutError(f"Workflow creation timed out after {REQUEST_TIMEOUT} seconds")
                    except Exception as e:
                        logger.error(f"Workflow creation failed: {e}")
                        raise
                
                logger.info(f"Workflow executed successfully: {workflow.data}")
                return workflow.data
                
            except CozeAPIError as e:
                error_code = getattr(e, 'code', None)
                error_msg = str(e)
                
                logger.error(f"Coze API error on attempt {attempt + 1}: code={error_code}, msg={error_msg}")
                
                # Handle specific error codes
                if error_code == 6039:
                    logger.error("Request interruption not supported - this request cannot be cancelled")
                    # For 6039 errors, wait longer before retry
                    adjusted_delay = retry_delay * REQUEST_RETRY_BACKOFF * (attempt + 1)
                elif error_code == 4100:
                    logger.error("Authentication error - check COZE_API_TOKEN")
                    # For auth errors, don't retry as frequently
                    adjusted_delay = retry_delay * 3
                elif error_code and str(error_code).startswith('5'):
                    logger.error("Server error - using exponential backoff")
                    adjusted_delay = retry_delay * (2 ** attempt)
                else:
                    adjusted_delay = retry_delay
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {adjusted_delay} seconds...")
                    
                    # Sleep with interruption check
                    sleep_start = time.time()
                    while time.time() - sleep_start < adjusted_delay:
                        if is_shutdown_requested():
                            logger.warning("Shutdown requested during retry delay")
                            return None
                        time.sleep(1)  # Check every second
                else:
                    logger.error("Max retries reached. Workflow execution failed.")
                    return None
                    
            except (Timeout, ConnectionError, RequestException, concurrent.futures.TimeoutError) as e:
                logger.error(f"Network/timeout error on attempt {attempt + 1}: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff for network errors
                    adjusted_delay = retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {adjusted_delay} seconds...")
                    
                    sleep_start = time.time()
                    while time.time() - sleep_start < adjusted_delay:
                        if is_shutdown_requested():
                            logger.warning("Shutdown requested during retry delay")
                            return None
                        time.sleep(1)
                else:
                    logger.error("Max retries reached. Workflow execution failed.")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    
                    sleep_start = time.time()
                    while time.time() - sleep_start < retry_delay:
                        if is_shutdown_requested():
                            logger.warning("Shutdown requested during retry delay")
                            return None
                        time.sleep(1)
                else:
                    logger.error("Max retries reached. Workflow execution failed.")
                    return None
        
        return None
        
    finally:
        with request_lock:
            active_requests -= 1

def health_check():
    """Simple health check function."""
    try:
        # Check if we can make a simple API call
        if coze_api_token and workflow_id:
            return {
                "status": "healthy",
                "timestamp": datetime.datetime.now().isoformat(),
                "active_requests": active_requests,
                "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
                "shutdown_requested": is_shutdown_requested()
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Missing required configuration",
                "timestamp": datetime.datetime.now().isoformat(),
                "active_requests": active_requests,
                "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
                "shutdown_requested": is_shutdown_requested()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat(),
            "active_requests": active_requests,
            "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
            "shutdown_requested": is_shutdown_requested()
        }

def scheduled_workflow_job():
    """The scheduled job that runs the workflow."""
    if is_shutdown_requested():
        logger.warning("Shutdown requested, skipping scheduled job")
        return
    
    logger.info("Starting scheduled workflow execution...")
    
    result = run_workflow_with_retry()
    
    if result:
        logger.info("Scheduled workflow completed successfully!")
    else:
        logger.error("Scheduled workflow failed after all retry attempts.")

def check_monthly_schedule(schedule_config: Dict[str, Any]) -> bool:
    """Check if it's time for monthly execution."""
    if schedule_config['type'] != 'monthly':
        return False
    
    now = datetime.datetime.now()
    target_day = schedule_config['day']
    target_time = schedule_config['time']
    
    # Check if today is the target day
    if now.day != target_day:
        return False
    
    # Check if current time matches target time
    current_time = now.strftime("%H:%M")
    return current_time == target_time

def run_scheduler():
    """Run the scheduler continuously with interruption support."""
    logger.info("Starting workflow scheduler...")
    logger.info(f"Request timeout: {REQUEST_TIMEOUT} seconds")
    logger.info(f"Max concurrent requests: {MAX_CONCURRENT_REQUESTS}")
    logger.info(f"Retry backoff multiplier: {REQUEST_RETRY_BACKOFF}")
    
    # Parse and setup schedule
    schedule_config = parse_schedule_config(SCHEDULE_CONFIG)
    setup_schedule(schedule_config)
    
    logger.info(f"Schedule configuration: {SCHEDULE_CONFIG}")
    logger.info(f"Timezone: {SCHEDULE_TIMEZONE}")
    logger.info(f"Max retries: {MAX_RETRIES}")
    logger.info(f"Retry delay: {RETRY_DELAY} seconds")
    
    # Run once immediately for testing (comment out in production)
    logger.info("Running workflow once for testing...")
    scheduled_workflow_job()
    
    # Keep the scheduler running
    check_interval = 60  # Check every minute
    last_health_check = time.time()
    
    while not is_shutdown_requested():
        try:
            current_time = time.time()
            
            # Periodic health check logging
            if current_time - last_health_check >= 300:  # Every 5 minutes
                health_status = health_check()
                logger.info(f"Health check: {health_status['status']}")
                if health_status['status'] != 'healthy':
                    logger.warning(f"Health check issues: {health_status}")
                last_health_check = current_time
            
            # Check monthly schedule if configured
            if schedule_config['type'] == 'monthly':
                if check_monthly_schedule(schedule_config):
                    scheduled_workflow_job()
            
            # Run pending scheduled tasks
            schedule.run_pending()
            
            # Sleep with interruption support
            sleep_start = time.time()
            while time.time() - sleep_start < check_interval:
                if is_shutdown_requested():
                    logger.info("Shutdown requested during sleep")
                    break
                time.sleep(1)  # Check every second
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Sleep with interruption support
            sleep_start = time.time()
            while time.time() - sleep_start < check_interval:
                if is_shutdown_requested():
                    logger.info("Shutdown requested during error recovery")
                    break
                time.sleep(1)
    
    logger.info("Scheduler shutdown complete")

def cleanup():
    """Cleanup function to be called on shutdown."""
    logger.info("Performing cleanup...")
    
    # Clear all scheduled jobs
    schedule.clear()
    
    # Wait for active requests to complete
    max_wait = 30  # Maximum 30 seconds to wait
    start_time = time.time()
    
    while active_requests > 0 and (time.time() - start_time) < max_wait:
        logger.info(f"Waiting for {active_requests} active requests to complete...")
        time.sleep(1)
    
    if active_requests > 0:
        logger.warning(f"Force shutdown with {active_requests} active requests remaining")
    else:
        logger.info("All active requests completed")

if __name__ == "__main__":
    logger.info("=== Coze Workflow Scheduler Starting ===")
    logger.info(f"Python version: {os.sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    try:
        run_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        cleanup()
        logger.info("=== Coze Workflow Scheduler Stopped ===")