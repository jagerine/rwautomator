import time
import sys
sys.path.insert(0, '/app')
from lib.db import get_pending_jobs 
import subprocess

print("Worker started, watching for pending jobs in database...")

while True:
    try:
        pending_jobs = get_pending_jobs()
        
        for job in pending_jobs:
            job_id = job['job_id']
            job_type = job['job_type']
            order_number = job['order_number']
            dc = job['distribution_center']
            current_status = job['status']
            
            if current_status == 'processing':
                print(f"Skipping job {job_id} as it is already processing")
                continue  
            
            print(f"Processing job: {job_id} ({job_type})")
            
            # Execute the job
            reset_order_job_types = ['reset_order', 'ResetOrder', 'Reset Single Order', 'Reset Batch Order']
            
            if job_type in reset_order_job_types:
                print(f"Attempt to reset order: {order_number} at DC: {dc}")
                result = subprocess.run(
                    ['python3', '/app/rw_automate.py', 'resetOrder', order_number, dc, job_id],
                    capture_output=True,
                    text=True
                )
                
                print(f"Subprocess completed for job {job_id} with return code {result.returncode}")
                
                success = result.returncode == 0
                output_message = result.stdout.strip()
                
                print(f"Job {job_id} {'completed' if success else 'failed'}")
                print(f"Output: {output_message}")
                

        time.sleep(3)  # Poll every X seconds

    except Exception as e:
        print(f"Worker error: {e}")
        time.sleep(5)