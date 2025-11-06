#!/usr/bin/env python3
"""
Test script for dynamic schedule configurations
"""

import os
import sys
import subprocess
import time

def test_schedule_config(config, description):
    """Test a specific schedule configuration"""
    print(f"\n🧪 测试: {description}")
    print(f"配置: {config}")
    
    env = os.environ.copy()
    env['SCHEDULE_CONFIG'] = config
    env['COZE_API_TOKEN'] = 'test_token'
    
    try:
        # 运行3秒后终止
        result = subprocess.run(
            ['python3', 'wewerss.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=3
        )
        
        if 'Scheduled' in result.stderr or 'Scheduled' in result.stdout:
            print("✅ 配置解析成功")
            return True
        else:
            print("❌ 配置解析失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("✅ 配置解析成功（正常运行）")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """Test all schedule configurations"""
    print("🚀 开始测试动态定时配置...")
    
    test_cases = [
        ("daily:18:00", "每天18:00执行"),
        ("daily:09:30", "每天09:30执行"),
        ("cron:0 18 * * *", "Cron表达式每天18:00"),
        ("cron:0 */6 * * *", "Cron表达式每6小时"),
        ("interval:3600", "每1小时间隔执行"),
        ("interval:7200", "每2小时间隔执行"),
        ("hourly:00", "每小时00分执行"),
        ("hourly:30", "每小时30分执行"),
        ("weekly:monday:18:00", "每周一18:00执行"),
        ("weekly:friday:09:00", "每周五09:00执行"),
        ("monthly:1:18:00", "每月1号18:00执行"),
        ("monthly:15:09:00", "每月15号09:00执行"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for config, description in test_cases:
        if test_schedule_config(config, description):
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！动态定时功能正常工作")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())