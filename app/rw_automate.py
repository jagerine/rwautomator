#!/usr/bin/env python3
"""
RealWorld Automation - Main Entry Point
Usage: python3 rw_automate.py <process> <args>
Example: python3 rw_automate.py resetOrder 408516 00 [job_id]
"""

import sys
import os
from lib.processes.reset_order import reset_order
from lib.processes.login import rwlogin
from lib.db import update_job_status
from dotenv import load_dotenv
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 rw_automate.py <process> <args>")
        print("\nAvailable processes:")
        print("  resetOrder <order_number> <distribution_center> [job_id]")
        sys.exit(1)
    
    process = sys.argv[1]
    
    if process == "resetOrder":
        if len(sys.argv) < 4:
            print("Error: resetOrder requires order number and distribution center")
            print("Usage: python3 rw_automate.py resetOrder <order_number> <distribution_center> [job_id]")
            sys.exit(1)
        
        order_number = sys.argv[2]
        distribution_center = sys.argv[3]
        job_id = sys.argv[4] if len(sys.argv) >= 5 else None
        
        print(f"Starting reset process for order: {order_number} (DC: {distribution_center})")
        
        # Update status to processing if we have a job_id
        if job_id:
            try:
                update_job_status(job_id, 'processing', increment_attempts=True)
            except Exception as e:
                print(f"Warning: Could not update job status: {e}")
        
        # Run the reset
        result, message = reset_order(order_number, distribution_center)
        
        # create_job_record(job_id, 'reset_order', order_number, distribution_center, rw_user) 
        
        
        # Update final status
        if job_id:
            try:
                if result:
                    log_path = f"/app/process-logs/reset_order_{distribution_center}_{order_number}_*.log"
                    print(f"✓ Order {order_number} reset completed successfully update status 1")
                    update_job_status(job_id, 'success',
                                    f'Reset completed successfully',
                                    log_path)
                else:
                    update_job_status(job_id, 'error',
                                    f'Reset failed: {message}')
            except Exception as e:
                print(f"Warning: Could not update final job status: {e}")
        
        # Exit with proper code based on result
        if result:
            update_job_status(job_id, 'success', 'Reset completed successfully')
            print(f"✓ Order {order_number} reset completed successfully update 2")
            sys.exit(0)
        else:
            update_job_status(job_id, 'error', f'Reset failed: {message}')
            print(f"✗ Order {order_number} :: reset failed: {message}")
            sys.exit(1)
    
    else:
        print(f"Error: Unknown process '{process}'")
        print("\nAvailable processes:")
        print("  resetOrder <order_number> <distribution_center> [job_id]")
        sys.exit(1)

if __name__ == "__main__":
    main()