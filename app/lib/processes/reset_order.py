"""
Reset Order Process
Handles the complete workflow to reset an order in RealWorld
"""

import pexpect
import time
import re
import os
import sys
from dotenv import load_dotenv
from lib.functions import setup_logger, get_valid_distribution_centers
load_dotenv()

# Force allocation of a PTY for pexpect
if not sys.stdin.isatty():
    # Running without a TTY (like from Flask), create a pseudo-terminal
    import pty
    master, slave = pty.openpty()
    os.environ['PEXPECT_FORCE_TTY'] = '1'

def reset_order(order_number, distribution_center="00"):
    """
    Reset an order in RealWorld system using pexpect
    
    Args:
        order_number: The order number to reset
        distribution_center: Distribution center ID (default: "00")
        employee_number: Employee number for login (default: "543")
        employee_password: Employee password (default: system default)
        host: Telnet host (default: 192.168.0.5)
        username: Telnet login username 
        user_password: Telnet login password
    
    Returns:
        bool: True if reset was successful, False otherwise
    """
    logger = setup_logger(distribution_center, order_number, "reset_order")
    child = None
    
    # Dictionary of valid distribution centers 
    valid_distribution_centers = get_valid_distribution_centers()
    
    if distribution_center not in valid_distribution_centers:
        logger.error(f"Invalid distribution center: {distribution_center}. Aborting reset.")
        return False, 'Invalid company / distribution center'

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    host = os.getenv('RW_HOST', '')
    port = os.getenv('RW_PORT', '23')
    username = os.getenv('RW_USERNAME', '')
    user_password = os.getenv('RW_PASSWORD', '')
    employee_number = os.getenv('RW_EMPLOYEE_NUMBER', '')
    employee_password = os.getenv('RW_EMPLOYEE_PASSWORD', '')

    try:
        # Connect to RealWorld via Telnet
        logger.info(f"Connecting to RealWorld at {host}:{port} with user {username}, employee {employee_number}")
        # print(f"\n=== Starting Reset Process for Order: {host} (DC: {distribution_center}) ===\n")
        child = pexpect.spawn(f'telnet {host} {port}', encoding='utf-8', timeout=30)
        
        # Login
        logger.info("Logging into RealWorld system")
        # print("=== Logging in ===")
        child.expect('login:')
        child.sendline(username)
        child.expect('Password:')
        child.sendline(user_password)
        time.sleep(3.5)
        
        if('Login incorrect' in child.before):
            logger.error("Login incorrect. Aborting reset.")
            return False, 'Login incorrect'
        
        # Wait for main menu
        # child.expect('your selection', timeout=40)
        child.expect([pexpect.TIMEOUT], timeout=2)
        time.sleep(1)
        
        # Navigate to accounting
        child.send('1\n')
        time.sleep(1)
        
        # print('\n=== FINAL OUTPUT ===\n')
        # print(child.before)
        # child.close()
        # print('\n=== END FINAL OUTPUT ===\n')
        # return False
        
        child.expect('company-ID', timeout=10)
        time.sleep(0.8)
        child.send(f'{distribution_center}\r')
        child.expect('Right company', timeout=5)
        child.send('\r')
        child.expect('Press ENTER to continue', timeout=5)
        child.send('\r')
        
        # Enter employee details
        child.expect('employee #', timeout=5)
        time.sleep(0.75)
        child.send(f'{employee_number}\r')
        child.expect('Any change', timeout=5)
        child.send('\r')
        child.expect('Please enter password', timeout=5)
        time.sleep(0.75)
        child.send(f'{employee_password}\r')
        time.sleep(1)
        
        # Get order total
        logger.info("Retrieving Ship Total")
        # print('=== Retrieving Ship Total ===')
        child.send('3\r')  # Order Entry
        time.sleep(1)
        child.send('2\r')  # View Order
        time.sleep(1)
        child.send('\r\r')  # Enter twice
        time.sleep(1)
        child.send(f'{order_number}\r')  # Order number    
        time.sleep(1.25)
        
        # does the screen say Order not on file ?
        child.expect([pexpect.TIMEOUT], timeout=2)
        if 'Order not on file' in child.before:
            logger.error(f'Order {order_number} not found in system. Aborting reset.')
            # print(f'*** ERROR: Order {order_number} not found in system. Aborting reset. ***')
            return False, 'Order not found in system'
        
        child.send('\x1b[13~')  # F3
        time.sleep(1.5)
        
        # Parse ship total
        child.expect([pexpect.TIMEOUT], timeout=1)

        ship_total = extract_ship_total(child.before)
        
        # if ship_total is not true 
        if not ship_total or ship_total == '0.00':
            logger.error(f'Could not retrieve valid ship total for order {order_number}. Aborting reset.')
            # print(f'*** ERROR: Could not retrieve valid ship total for order {order_number}. Aborting reset. ***')
            return False, 'Could not find a ship total'
        
        # print(f'Ship Total for Order {order_number}: {ship_total}\n')
        logger.info(f'Ship total for order {order_number}: {ship_total}')
        
        # Navigate back to menu
        # print('=== Navigating back to reset menu ===')
        logger.info("Navigating back to reset menu")
        child.send('\t\t\r\t\t')  # TAB TAB ENTER TAB TAB
        time.sleep(3)
        
        # Go to reset menu
        # print('=== Going to reset menu ===')
        logger.info("Navigating to reset order menu")
        child.send('8\r')
        time.sleep(2)
        child.send('22\r')
        time.sleep(2)
        
        # Enter order details
        # print('=== Entering order for reset ===')
        logger.info("Entering order details for reset")
        child.send('\r')  # Move to next field
        time.sleep(1)
        child.send(f'{order_number}\r')  # Order number
        time.sleep(2)
        child.send('\r\r')  # ENTER twice
        time.sleep(2)
        
        # Confirm and enter ship total
        # print('=== Confirming and entering ship total ===')
        logger.info("Confirming reset and entering ship total")
        child.send('Y\r')  # Yes to confirmation
        time.sleep(2)
        child.send(f'{ship_total}\r')  # Enter ship total
        time.sleep(2)
        child.send('Y\r')  # Final confirmation
        time.sleep(3)
        
        # Check for completion
        # print('=== Checking for completion ===')
        logger.info("Checking for reset completion")
        child.expect([pexpect.TIMEOUT], timeout=10)
        final_output = child.before

        if 'Procedure complete' in final_output or 'Procedure Complete' in final_output:
            print('SUCCESS! Order reset completed!')
            logger.info("Order reset completed successfully")
            return True, 'Reset completed successfully'
        else:
            # print('WARNING: Did not find "Procedure Complete"')
            logger.warning('Did not find "Procedure Complete"')
            logger.warning(f"Final output received:\n\n{final_output}")
            # print('\n=== FINAL OUTPUT ===')
            # print(final_output)
            return False, 'Reset failed'
    
    except Exception as e:
        print(f"Error during reset process: {e}")
        logger.error(f"Exception during reset process: {e}")
        return False, 'Reset failed'
    
    finally:
        if child:
            try:
                child.close()
            except:
                pass
            
def strip_ansi_codes(text):
    """Remove ANSI escape sequences from text"""
    # Pattern matches: ESC [ ... m  or  ESC [ ... H  etc.
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    return ansi_escape.sub('', text)

def extract_ship_total(text):
    """
    Extract ship total from given text.
    
    Args:
        text (str): The text to search for ship total
    
    Returns:
        str: The extracted ship total, or '0.00' if not found
    """
    
    clean_output = strip_ansi_codes(text)
    
    if not 'Ship total' in clean_output:
        print('ERROR: "Ship total" not found')
        return None
    
    idx = clean_output.index('Ship total')
    idx += len('Ship total')
    
    # Skip to first digit
    while idx < len(clean_output) and not clean_output[idx].isdigit():
        idx += 1
    
    # Collect the number
    ship_total = ''
    while idx < len(clean_output) and (clean_output[idx].isdigit() or clean_output[idx] == '.'):
        ship_total += clean_output[idx]
        idx += 1
    
    if ship_total:
        print(f'SUCCESS! Ship total: {ship_total}')
        return ship_total
    else:
        print('ERROR: Found "Ship total" but no number')
        return None