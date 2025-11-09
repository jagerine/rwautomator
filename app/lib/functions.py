import os
import pexpect
import logging
import time
from datetime import datetime
from dotenv import load_dotenv


def get_real_world_connection():
    """
    Establish a telnet connection to RealWorld system with enhanced logging
    
    Returns:
        pexpect.spawn: Telnet connection object
    """
    try:
        # Get connection details from environment variables
        host = os.getenv('RW_HOST', '192.168.0.5')
        port = os.getenv('RW_TELNET_PORT', '23')
        
        print(f"Attempting to connect to {host}:{port}")
        
        # Log connection attempt details
        logger = logging.getLogger('telnet_connection')
        logger.info(f'Attempting to connect to {host}:{port}')
        
        # Create the spawn connection with increased timeout
        child = pexpect.spawn(f'telnet {host} {port}', encoding='utf-8', timeout=30)
        
        # Enable logging of all interactions
        log_file = open('/tmp/telnet_interaction.log', 'wb')
        child.logfile = log_file
        
        # Additional logging to help diagnose connection issues
        print("Telnet connection initiated")
        logger.info("Telnet connection initiated")
        
        return child
    
    except Exception as e:
        print(f"CRITICAL CONNECTION ERROR: {e}")
        logger.error(f"Failed to establish telnet connection: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_env_if_needed():
    if not os.getenv('RW_EMPLOYEE_NUMBER'):
        load_dotenv()


def get_valid_distribution_centers():
    """
    Retrieve a list of valid distribution centers from environment variable.
    
    Returns:
        list: List of valid distribution center codes
    """
    
    locations = {
        "00": "NASSAU CANDY DISTRIBUTORS INC",
        "01": "NASSAU CANDY SOUTH",
        "02": "NASSAU GOURMET FOODS",
        "03": "STELLAR TRACKING COMPANY",
        "04": "NASSAU CANDY MIDWEST",
        "05": "NASSAU CANDY WEST-LA",
        "06": "NC CHOCOLATE MANUFACTURING LLC",
        "07": "NASSAU CANDY SOUTHWEST",
        "08": "NASSAU CANDY WEST-SSF",
        "09": "THE CHOCOLATE INN",
        "10": "NASSAU CANDY WEST-COPY"
    }

    return locations

def setup_logger(distribution_center, order_number, process_name):
    try:
        # Create logs directory structure
        current_date = datetime.now()
        log_dir = os.path.join(
            '/app/process-logs',
            current_date.strftime('%Y'), 
            current_date.strftime('%m'), 
            current_date.strftime('%d')
        )
        
        # Ensure the directory exists with full permissions
        os.makedirs(log_dir, exist_ok=True)
        os.chmod(log_dir, 0o777)
        
        # Create log filename with distribution center, order number, and epoch time
        log_filename = os.path.join(
            log_dir,
            f"{process_name}_{distribution_center}_{order_number}_{int(time.time())}.log"
        )
        
        # Print debug information
        print(f"Attempting to create log file: {log_filename}")
        
        # Configure logger
        logger = logging.getLogger(f'reset_order_{order_number}')
        logger.handlers.clear()
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        
        # Create file handler
        try:
            file_handler = logging.FileHandler(log_filename)
            file_handler.setLevel(logging.DEBUG)
        except Exception as file_error:
            print(f"Error creating file handler: {file_error}")
            raise
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Log a test message
        logger.info(f"Log file created")
        
        return logger
    
    except Exception as e:
        print(f"CRITICAL ERROR in setup_logger: {e}")
        # Fallback to basic logging if custom setup fails
        logging.basicConfig(level=logging.DEBUG)
        return logging.getLogger(f'reset_order_{order_number}')