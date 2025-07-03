#!/usr/bin/env python3
"""
Production health check for Senate Hearing Audio Capture
Simple health check script for monitoring and alerting
"""

import asyncio
import argparse
import json
import sys
import time
import httpx
from typing import Dict, Optional

class ProductionHealthCheck:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    async def check_health(self) -> Dict:
        """Check application health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'data': response.json()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'response_time': response.elapsed.total_seconds()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }
            
    async def check_database(self) -> Dict:
        """Check database connectivity"""
        try:
            response = await self.client.get(f"{self.base_url}/api/system/health/database")
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'data': response.json()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'response_time': response.elapsed.total_seconds()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }
            
    async def check_redis(self) -> Dict:
        """Check Redis connectivity"""
        try:
            response = await self.client.get(f"{self.base_url}/api/system/health/redis")
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'data': response.json()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'response_time': response.elapsed.total_seconds()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }
            
    async def check_processing(self) -> Dict:
        """Check processing capability"""
        try:
            test_payload = {
                "hearing_id": "health-check-test",
                "dry_run": True
            }
            
            response = await self.client.post(f"{self.base_url}/api/process/hearing", json=test_payload)
            if response.status_code in [200, 202]:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'data': response.json()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'response_time': response.elapsed.total_seconds()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }
            
    async def run_comprehensive_check(self) -> Dict:
        """Run comprehensive health check"""
        start_time = time.time()
        
        # Run all checks
        health_check = await self.check_health()
        database_check = await self.check_database()
        redis_check = await self.check_redis()
        processing_check = await self.check_processing()
        
        total_time = time.time() - start_time
        
        # Determine overall status
        all_checks = [health_check, database_check, redis_check, processing_check]
        healthy_count = sum(1 for check in all_checks if check['status'] == 'healthy')
        overall_status = 'healthy' if healthy_count == len(all_checks) else 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'timestamp': time.time(),
            'total_time': total_time,
            'checks': {
                'application': health_check,
                'database': database_check,
                'redis': redis_check,
                'processing': processing_check
            },
            'summary': {
                'healthy_checks': healthy_count,
                'total_checks': len(all_checks),
                'health_percentage': (healthy_count / len(all_checks)) * 100
            }
        }

async def main():
    parser = argparse.ArgumentParser(description='Production Health Check for Senate Hearing Audio Capture')
    parser.add_argument('--url', required=True, help='Base URL of the deployed application')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--output', help='Output file for health check results (JSON format)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    async with ProductionHealthCheck(args.url, args.timeout) as health_check:
        result = await health_check.run_comprehensive_check()
        
        if args.verbose:
            print(f"Health Check Results for {args.url}")
            print("=" * 50)
            print(f"Overall Status: {result['overall_status'].upper()}")
            print(f"Total Time: {result['total_time']:.2f}s")
            print(f"Health Percentage: {result['summary']['health_percentage']:.1f}%")
            print("\nComponent Status:")
            
            for component, check in result['checks'].items():
                status_icon = "✅" if check['status'] == 'healthy' else "❌"
                response_time = f"{check['response_time']:.2f}s" if check['response_time'] else "N/A"
                print(f"  {status_icon} {component.capitalize()}: {check['status']} ({response_time})")
                
                if check['status'] == 'unhealthy':
                    print(f"    Error: {check['error']}")
        else:
            # Simple output for monitoring scripts
            status_icon = "✅" if result['overall_status'] == 'healthy' else "❌"
            print(f"{status_icon} {result['overall_status'].upper()} - {result['summary']['health_percentage']:.1f}% healthy")
            
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
                
        # Exit with appropriate code
        sys.exit(0 if result['overall_status'] == 'healthy' else 1)

if __name__ == "__main__":
    asyncio.run(main())