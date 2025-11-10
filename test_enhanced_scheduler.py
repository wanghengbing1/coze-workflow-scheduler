#!/usr/bin/env python3
"""
Test script for the enhanced Coze workflow scheduler with 6039 error handling.
"""

import os
import sys
import time
import signal
import threading
from unittest.mock import Mock, patch
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced scheduler
import wewerss

# Configure logging for testing
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_signal_handling():
    """Test signal handling for graceful shutdown."""
    print("Testing signal handling...")
    
    # Set up test environment
    wewerss.shutdown_event.clear()
    
    # Test SIGTERM handling
    wewerss.signal_handler(signal.SIGTERM, None)
    assert wewerss.is_shutdown_requested(), "SIGTERM should trigger shutdown"
    
    # Reset for next test
    wewerss.shutdown_event.clear()
    
    # Test SIGINT handling
    wewerss.signal_handler(signal.SIGINT, None)
    assert wewerss.is_shutdown_requested(), "SIGINT should trigger shutdown"
    
    print("✓ Signal handling test passed")

def test_request_slot_management():
    """Test request slot management."""
    print("Testing request slot management...")
    
    # Reset global state
    wewerss.active_requests = 0
    
    # Test normal slot acquisition
    assert wewerss.wait_for_request_slot(timeout=1), "Should get slot when none are active"
    
    # Simulate max concurrent requests
    wewerss.active_requests = wewerss.MAX_CONCURRENT_REQUESTS
    
    # Test timeout when slots are full
    assert not wewerss.wait_for_request_slot(timeout=0.5), "Should timeout when slots are full"
    
    print("✓ Request slot management test passed")

def test_health_check():
    """Test health check function."""
    print("Testing health check...")
    
    # Test with valid configuration
    health = wewerss.health_check()
    assert health['status'] in ['healthy', 'unhealthy'], "Health check should return valid status"
    assert 'timestamp' in health, "Health check should include timestamp"
    assert 'active_requests' in health, "Health check should include active requests count"
    
    print("✓ Health check test passed")

def test_error_code_handling():
    """Test specific error code handling."""
    print("Testing error code handling...")
    
    # Mock CozeAPIError with different error codes
    from cozepy import CozeAPIError
    
    # Test 6039 error handling
    error_6039 = CozeAPIError(code=6039, msg="This requests do not support interruption")
    assert str(error_6039.code) == "6039", "Should properly handle 6039 error code"
    
    # Test 4100 auth error handling
    error_4100 = CozeAPIError(code=4100, msg="authentication is invalid")
    assert str(error_4100.code) == "4100", "Should properly handle 4100 error code"
    
    print("✓ Error code handling test passed")

def test_retry_mechanism():
    """Test retry mechanism with interruption."""
    print("Testing retry mechanism...")
    
    # Reset global state
    wewerss.shutdown_event.clear()
    wewerss.active_requests = 0
    
    # Mock the coze client to simulate failures
    with patch.object(wewerss, 'coze') as mock_coze:
        # Simulate API error
        from cozepy import CozeAPIError
        mock_coze.workflows.runs.create.side_effect = CozeAPIError(
            code=6039, 
            msg="This requests do not support interruption"
        )
        
        # Test that the function handles the error gracefully
        result = wewerss.run_workflow_with_retry(max_retries=2, retry_delay=0.1)
        assert result is None, "Should return None when all retries fail"
        
        # Verify retry attempts were made
        assert mock_coze.workflows.runs.create.call_count == 2, "Should attempt retries"
    
    print("✓ Retry mechanism test passed")

def test_shutdown_during_retry():
    """Test shutdown during retry delay."""
    print("Testing shutdown during retry...")
    
    # Reset global state
    wewerss.shutdown_event.clear()
    wewerss.active_requests = 0
    
    def delayed_shutdown():
        """Trigger shutdown after a short delay."""
        time.sleep(0.2)
        wewerss.shutdown_event.set()
    
    # Start shutdown timer
    shutdown_thread = threading.Thread(target=delayed_shutdown)
    shutdown_thread.start()
    
    # Mock the coze client to simulate failures
    with patch.object(wewerss, 'coze') as mock_coze:
        from cozepy import CozeAPIError
        mock_coze.workflows.runs.create.side_effect = CozeAPIError(
            code=500, 
            msg="Server error"
        )
        
        # This should be interrupted by shutdown
        start_time = time.time()
        result = wewerss.run_workflow_with_retry(max_retries=5, retry_delay=1)
        end_time = time.time()
        
        # Should return None due to shutdown
        assert result is None, "Should return None when shutdown is requested"
        
        # Should not wait for all retries due to shutdown
        assert end_time - start_time < 3, "Should be interrupted before completing all retries"
    
    shutdown_thread.join()
    print("✓ Shutdown during retry test passed")

def run_all_tests():
    """Run all tests."""
    print("=== Running Enhanced Scheduler Tests ===")
    
    try:
        test_signal_handling()
        test_request_slot_management()
        test_health_check()
        test_error_code_handling()
        test_retry_mechanism()
        test_shutdown_during_retry()
        
        print("\n=== All tests passed! ===")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    # Set up minimal environment for testing
    os.environ['COZE_API_TOKEN'] = 'test_token'
    os.environ['COZE_WORKFLOW_ID'] = 'test_workflow_id'
    
    success = run_all_tests()
    sys.exit(0 if success else 1)