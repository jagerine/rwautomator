import pyodbc
import os
from datetime import datetime

def get_connection():
    """Create and return a SQL Server connection"""
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('MSSQL_SERVER')};"
        f"DATABASE={os.getenv('MSSQL_DATABASE')};"
        f"UID={os.getenv('MSSQL_USERNAME')};"
        f"PWD={os.getenv('MSSQL_PASSWORD')};"
        f"TrustServerCertificate=yes;"  # Allowing self-signed cert
    )
    return pyodbc.connect(conn_str)

def create_job_record(job_id, job_type, order_number, distribution_center, rw_user=None, ticket_number=''):
    """Create initial job record with pending status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO RwAutomator_Log 
        (job_id, job_type, order_number, distribution_center, rw_user, status, ticket_number)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
    """, (job_id, job_type, order_number, distribution_center, rw_user, ticket_number))
    
    conn.commit()
    conn.close()

def get_pending_jobs():
    """Get all pending jobs"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT job_id, job_type, order_number, distribution_center, send_attempts, 
        response_data , status, requested_at, started_at, completed_at, result_message
        FROM RwAutomator_Log 
        WHERE status not in('success', 'failed' )
        ORDER BY requested_at ASC
    """)
    
    jobs = []
    for row in cursor.fetchall():
        jobs.append({
            'job_id': row[0],
            'job_type': row[1],
            'order_number': row[2],
            'distribution_center': row[3],
            'send_attempts': row[4],
            'response_data': row[5],
            'status': row[6],
            'requested_at': row[7].isoformat() if row[7] else None,
            'started_at': row[8].isoformat() if row[8] else None,
            'completed_at': row[9].isoformat() if row[9] else None,
            'result_message': row[10] if row[10] else None 
        })
    
    conn.close()
    return jobs

def get_job_status(job_id):
    """Get current status of a job"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT status, result_message, send_attempts
        FROM RwAutomator_Log
        WHERE job_id = ?
    """, (job_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {'status': row[0], 'message': row[1], 'send_attempts': row[2]}
    return None

def get_job_history(page=1, per_page=50, order_number='', start_date='', end_date='', status=''):
    """Get paginated job history with optional filters"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build WHERE clause dynamically
    where_clauses = []
    params = []
    
    if order_number:
        where_clauses.append("order_number LIKE ?")
        params.append(f'%{order_number}%')
    
    if start_date:
        where_clauses.append("requested_at >= ?")
        params.append(start_date)
    
    if end_date:
        where_clauses.append("requested_at <= ?")
        params.append(end_date + ' 23:59:59')  # Include entire end date
    
    if status:
        where_clauses.append("status = ?")
        params.append(status)
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Pagination work
    count_query = f"SELECT COUNT(*) FROM RwAutomator_Log {where_sql}"
    cursor.execute(count_query, params)
    total_records = cursor.fetchone()[0]

    total_pages = (total_records + per_page - 1) // per_page 
    offset = (page - 1) * per_page
    
    data_query = f"""
        SELECT 
            job_id, job_type, order_number, distribution_center, rw_user,
            status, result_message, requested_at, started_at, completed_at, 
            ticket_number, send_attempts
        FROM RwAutomator_Log
        {where_sql}
        ORDER BY requested_at DESC
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
    """
    
    cursor.execute(data_query, params + [offset, per_page])
    
    jobs = []
    for row in cursor.fetchall():
        jobs.append({
            'job_id': row[0],
            'job_type': row[1],
            'order_number': row[2],
            'distribution_center': row[3],
            'rw_user': row[4],
            'status': row[5],
            'result_message': row[6],
            'requested_at': row[7].isoformat() if row[7] else None,
            'started_at': row[8].isoformat() if row[8] else None,
            'completed_at': row[9].isoformat() if row[9] else None,
            'ticket_number': row[10],
            'send_attempts': row[11]
        })
    
    conn.close()
    
    return {
        'jobs': jobs,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_records': total_records,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
    }

def get_job_record(job_id):
    """Get full job record by job_id"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT job_id, job_type, order_number, distribution_center, rw_user,
               status, result_message, requested_at, started_at, completed_at, send_attempts
        FROM RwAutomator_Log
        WHERE job_id = ?
    """, (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'job_id': row[0],
            'job_type': row[1],
            'order_number': row[2],
            'distribution_center': row[3],
            'rw_user': row[4],
            'status': row[5],
            'result_message': row[6],
            'requested_at': row[7].isoformat() if row[7] else None,
            'started_at': row[8].isoformat() if row[8] else None,
            'completed_at': row[9].isoformat() if row[9] else None,
            'send_attempts': row[10]
        }
    return None

def update_job_status(job_id, status, result_message=None, log_file_path=None, increment_attempts=False):
    """Update job status and optionally set completion time"""
    conn = get_connection()
    cursor = conn.cursor()
    
    job = get_job_record(job_id)
    max_attempts = 3
    
    if status == 'processing':
        if increment_attempts:
            cursor.execute("""
                UPDATE RwAutomator_Log 
                SET status = ?, started_at = GETDATE(), send_attempts = send_attempts + 1
                WHERE job_id = ?
            """, (status, job_id))
        else:
            cursor.execute("""
                UPDATE RwAutomator_Log 
                SET status = ?, started_at = GETDATE() 
                WHERE job_id = ?
            """, (status, job_id))
    elif status in ('success', 'error'):
        cursor.execute("""
            UPDATE RwAutomator_Log 
            SET status = ?, result_message = ?, log_file_path = ?, completed_at = GETDATE()
            WHERE job_id = ?
        """, (status, result_message, log_file_path, job_id))
    else:
        if increment_attempts:
            cursor.execute("""
                UPDATE RwAutomator_Log 
                SET status = ?, send_attempts = send_attempts + 1
                WHERE job_id = ?
            """, (status, job_id))
        else:
            cursor.execute("""
                UPDATE RwAutomator_Log 
                SET status = ?
                WHERE job_id = ?
            """, (status, job_id))
            
    current_attempts = job['send_attempts'] if job else 0
    if increment_attempts:
        current_attempts += 1
        
    if current_attempts >= max_attempts and status != 'success':
        append_message = f" Maximum attempts ({max_attempts}) reached."
        if result_message:
            result_message += append_message
        else:
            result_message = append_message.strip()
        cursor.execute("""
            UPDATE RwAutomator_Log 
            SET status = 'failed', result_message = ?, completed_at = GETDATE()
            WHERE job_id = ?
        """, (result_message, job_id))

    conn.commit()
    conn.close()