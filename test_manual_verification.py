"""
Manual verification script to test the fix.
This script can be run to manually verify the application behavior.
"""

import subprocess
import time
import sys
import os
import requests

def test_with_database():
    """Test application with MySQL available."""
    print("\n" + "="*60)
    print("TEST 1: Application with MySQL available")
    print("="*60)
    
    # Use current environment (MySQL should be available)
    env = os.environ.copy()
    env['PORT'] = '8003'
    
    process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8003'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        time.sleep(5)
        
        # Check if process is running
        if process.poll() is not None:
            print("❌ FAILED: Application crashed")
            return False
        
        # Check health endpoint
        response = requests.get('http://localhost:8003/health', timeout=5)
        data = response.json()
        
        print(f"✓ Application started successfully")
        print(f"✓ Health check: {data}")
        print(f"✓ Database available: {data.get('database', False)}")
        
        if data.get('database') == True:
            print("✓ TEST PASSED: Application works with database")
            return True
        else:
            print("❌ TEST FAILED: Database should be available")
            return False
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def test_without_database():
    """Test application without MySQL available."""
    print("\n" + "="*60)
    print("TEST 2: Application without MySQL available")
    print("="*60)
    
    # Set environment to unavailable MySQL
    env = os.environ.copy()
    env['MYSQL_HOST'] = 'nonexistent-host.invalid'
    env['MYSQL_PORT'] = '3306'
    env['PORT'] = '8004'
    
    process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8004'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        time.sleep(5)
        
        # Check if process is running
        if process.poll() is not None:
            print("❌ FAILED: Application crashed (this is the bug!)")
            return False
        
        # Check health endpoint
        response = requests.get('http://localhost:8004/health', timeout=5)
        data = response.json()
        
        print(f"✓ Application started successfully WITHOUT database")
        print(f"✓ Health check: {data}")
        print(f"✓ Database available: {data.get('database', False)}")
        
        if data.get('database') == False:
            print("✓ TEST PASSED: Application works without database")
            return True
        else:
            print("❌ TEST FAILED: Database should NOT be available")
            return False
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("RAILWAY DEPLOYMENT CRASH FIX - MANUAL VERIFICATION")
    print("="*60)
    
    test1_passed = test_with_database()
    test2_passed = test_without_database()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Test 1 (with database): {'✓ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (without database): {'✓ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✓ ALL TESTS PASSED - Fix is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Fix needs adjustment")
        sys.exit(1)
