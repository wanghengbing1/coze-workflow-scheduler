"""
This example describes how to use the workflow interface to chat with dynamic scheduling and retry mechanisms.
"""

import os
import time
import datetime
import logging
from typing import Optional, Dict, Any
import schedule
from croniter import croniter

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

# Get configuration from environment variables
coze_api_token = os.getenv('COZE_API_TOKEN', '')
coze_api_base = os.getenv('COZE_API_BASE', 'https://api.coze.cn')
workflow_id = os.getenv('COZE_WORKFLOW_ID', '756925844681878738')

# Dynamic scheduling configuration
SCHEDULE_CONFIG = os.getenv('SCHEDULE_CONFIG', 'daily:18:00')  # 默认每天18:00
SCHEDULE_TIMEZONE = os.getenv('SCHEDULE_TIMEZONE', 'UTC')  # 默认UTC时区
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '5'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '60'))

# Validate required environment variables
if not coze_api_token:
    logger.error("COZE_API_TOKEN environment variable is required")
    exit(1)

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa

# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

def parse_schedule_config(config: str) -> Dict[str, Any]:
    """
    Parse schedule configuration string.
    
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
        parts = config.split(':')
        schedule_type = parts[0].lower()
        
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
    Run the workflow with retry mechanism.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retry attempts
        
    Returns:
        Workflow result data if successful, None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to run workflow (attempt {attempt + 1}/{max_retries})")
            
            # Call the coze.workflows.runs.create method to create a workflow run
            workflow = coze.workflows.runs.create(
                workflow_id=workflow_id,
            )
            
            logger.info(f"Workflow executed successfully: {workflow.data}")
            return workflow.data
            
        except CozeAPIError as e:
            logger.error(f"Coze API error on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Workflow execution failed.")
                return None
                
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Workflow execution failed.")
                return None
    
    return None

def scheduled_workflow_job():
    """The scheduled job that runs the workflow."""
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
    """Run the scheduler continuously."""
    logger.info("Starting workflow scheduler...")
    
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
    while True:
        try:
            # Check monthly schedule if configured
            if schedule_config['type'] == 'monthly':
                if check_monthly_schedule(schedule_config):
                    scheduled_workflow_job()
            
            # Run pending scheduled tasks
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}")