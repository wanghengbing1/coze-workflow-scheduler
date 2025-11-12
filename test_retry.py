#!/usr/bin/env python3
"""
测试重试机制的简单脚本
"""

import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class TestRetry:
    def __init__(self):
        self.attempt_count = 0
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception_type(Exception)
    )
    def test_function(self):
        """测试函数，前两次失败，第三次成功"""
        self.attempt_count += 1
        print(f"尝试第 {self.attempt_count} 次")
        
        if self.attempt_count < 3:
            print(f"第 {self.attempt_count} 次失败，将重试...")
            raise Exception(f"模拟失败 {self.attempt_count}")
        else:
            print("第 3 次成功！")
            return "成功结果"

if __name__ == "__main__":
    tester = TestRetry()
    try:
        result = tester.test_function()
        print(f"最终结果: {result}")
        print(f"总尝试次数: {tester.attempt_count}")
    except Exception as e:
        print(f"所有重试都失败了: {e}")